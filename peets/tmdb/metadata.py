from __future__ import annotations

import dataclasses
import itertools
from datetime import datetime
from functools import singledispatchmethod
from typing import TypeVar

import tmdbsimple as tmdb
from dateutil.parser import isoparse

from peets.entities import (
    MediaAiredStatus,
    MediaArtwork,
    MediaCertification,
    MediaFileType,
    MediaGenres,
    MediaRating,
    Movie,
    MovieSet,
    Person,
    PersonType,
    TvShow,
)
from peets.iso import Country, Language
from peets.merger import ConvertTable, Option, replace
from peets.scraper import MetadataProvider, Provider, SearchResult

from .config import _ARTWORK_BASE_URL, _PROFILE_BASE_URL, PROVIDER_ID


class TmdbMovieMetadata(MetadataProvider[Movie]):
    T = TypeVar("T", Movie, TvShow)

    def __init__(
        self,
        language: Language,
        country: Country,
        include_adult: bool = True,
    ) -> None:
        super().__init__()

        self.language = f"{language.name}-{country.name}".lower()
        self.country = country.name
        self.include_adult = include_adult

        self.fallback_country = Country.US.name
        self.fallback_lan = "en-us"

    @property
    def available_type(self) -> list[str]:
        return ["movie", "tvshow"]

    @singledispatchmethod
    def search(self, media: T) -> list[SearchResult]:
        raise NotImplementedError()

    @singledispatchmethod
    def apply(self, media: T, **kwargs) -> T:
        raise NotImplementedError()

    @search.register
    def _(self, movie: Movie) -> list[SearchResult]:
        api = tmdb.Search()
        resp = api.movie(
            language=self.language,
            query=movie.title,
            include_adult=self.include_adult,
            year=movie.year,
        )
        return [
            SearchResult(
                d["id"], d["title"], "tmdb", d["release_date"], d["popularity"]
            )
            for d in api.results
        ]

    @apply.register
    def _(self, movie: Movie, **kwargs) -> Movie:
        m_id = kwargs["id_"]
        api = tmdb.Movies(m_id)
        context = api.info(
            language=self.language, append_to_response="credits,keywords,release_dates"
        )

        table: ConvertTable = [
            (
                "ids",
                lambda imdb_id: ("imdb", str(imdb_id)),
            ),  # dict 类型的返回 (key value)
            ("ids", lambda id: (PROVIDER_ID, str(id))),
            ("plot", "overview"),
            (
                "ratings",
                lambda vote_average, vote_count: (
                    PROVIDER_ID,
                    MediaRating(
                        rating_id="tmdb", rating=vote_average, votes=vote_count
                    ),
                ),
            ),
            (
                "artwork_url_map",  # TODO artwork 应该另外处理？
                lambda poster_path, id: (
                    MediaFileType.POSTER,
                    f"{_ARTWORK_BASE_URL}original{poster_path}",
                )
                # MediaArtwork(
                #     provider_id=PROVIDER_ID,
                #     artwork_type=MediaArtworkType.POSTER,
                #     preview_url=f"{artwork_base_url}w342{path}",
                #     default_url=f"{artwork_base_url}original{path}",
                #     original_url=f"{artwork_base_url}original{path}",
                #     language=language,
                #     tmdbId=id_
            ),  # 列表类型，返回单项表示插入？？
            (
                "spoken_languages",
                lambda spoken_languages: ", ".join(
                    [lang["iso_639_1"] for lang in spoken_languages]
                ),
            ),
            (
                "country",
                lambda production_countries: ", ".join(
                    [country["iso_3166_1"] for country in production_countries]
                ),
            ),
            (
                "production_company",
                lambda production_companies: ", ".join(
                    [company["name"] for company in production_companies]
                ),
            ),
            # 一对多的情况下，支持通过 tuple 指定
            # 转换函数表示默认赋值
            (
                "year",
                lambda release_date: datetime.strptime(release_date, "%Y-%m-%d").year,
            ),
            (
                "release_date",
                lambda release_dates, production_countries: self._parse_release_date(
                    release_dates, production_countries
                ),
            ),
            (
                "certification",
                lambda release_dates, production_countries: self._parse_certification(
                    release_dates, production_countries
                ),
            ),
            # credits TODO partition
            *zip(
                ("actors", "producers", "directors", "writers"),
                (
                    _credits_filter(PersonType.ACTOR),
                    _credits_filter(PersonType.PRODUCER),
                    _credits_filter(PersonType.DIRECTOR),
                    _credits_filter(PersonType.WRITER),
                ),
            ),
            # genres
            ("genres", lambda genres: [_to_genre(g) for g in genres]),
            ("genres", lambda adult: MediaGenres.EROTIC if adult else []),
            (
                ("movie_set", "ids"),
                lambda belongs_to_collection: (
                    MovieSet(name=belongs_to_collection["name"], tmdb_id=belongs_to_collection["id"]),
                    ("tmdbSet", str(belongs_to_collection["id"])),
                ),
                Option.KEY_NOT_EXIST_IGNORE_ANY,
            ),
            ("tags", lambda keywords: [k["name"] for k in keywords["keywords"]]),
        ]

        return replace(movie, context, table)

    @search.register
    def _(self, tvshow: TvShow) -> list[SearchResult]:
        api = tmdb.Search()
        resp = api.tv(
            language=self.language,
            query=tvshow.title,
            include_adult=self.include_adult,
            year=tvshow.year,
        )
        return [
            SearchResult(
                d["id"],
                d["name"],
                "tmdb",
                int(d["first_air_date"][0:4]),
                d["popularity"],
            )
            for d in api.results
        ]

    @apply.register
    def _(self, tvshow: TvShow, **kwargs) -> TvShow:
        m_id = kwargs["id_"]

        episode_table: ConvertTable = [
            # TODO external ids 需要调用 episode api
            ("ids", lambda id: (PROVIDER_ID, str(id))),
            ("season", "season_number"),
            ("episode", "episode_number"),
            ("title", "name"),
            ("plot", "overview"),
            (
                "ratings",
                lambda vote_average, vote_count: (
                    PROVIDER_ID,
                    MediaRating(
                        rating_id="tmdb", rating=vote_average, votes=vote_count
                    ),
                ),
            ),
            ("first_aired", "air_date"),
            *zip(
                ("directors", "writers"),
                (_crew_filter(PersonType.DIRECTOR), _crew_filter(PersonType.WRITER)),
            ),
            (
                "actors",
                lambda guest_stars: [
                    _conv_people(c, PersonType.ACTOR) for c in guest_stars
                ],
            ),
            (
                "artwork_url_map",  # TODO artwork 应该另外处理？
                lambda still_path, id: (
                    MediaFileType.THUMB,
                    f"{_ARTWORK_BASE_URL}original{still_path}",
                ),
            ),
        ]
        episodes = []
        for key, group in itertools.groupby(tvshow.episodes, lambda e: e.season):
            season_context = tmdb.TV_Seasons(m_id, key).info(language=self.language)
            for episode in group:
                context = season_context["episodes"][episode.episode - 1]
                episodes.append(replace(episode, context, episode_table))

        api = tmdb.TV(m_id)
        tv_context = api.info(
            language=self.language,
            append_to_response="credits, external_ids, content_ratings, keywords",
        )
        season_table: ConvertTable = [
            ("plot", "overview"),
            ("season", "season_number"),
            (
                "artwork_url_map",  # TODO artwork 应该另外处理？
                lambda poster_path: (
                    MediaFileType.POSTER,
                    f"{_ARTWORK_BASE_URL}original{poster_path}",
                ),
            ),
        ]
        # lambda 表达式语法太繁琐
        table: ConvertTable = [
            ("ids", lambda id: (PROVIDER_ID, str(id))),
            ("title", "name"),
            ("first_aired", "first_air_date"),
            ("plot", "overview"),
            (
                "ratings",
                lambda vote_average, vote_count: (
                    PROVIDER_ID,
                    MediaRating(
                        rating_id="tmdb", rating=vote_average, votes=vote_count
                    ),
                ),
            ),
            (
                "country",
                lambda origin_country: ", ".join(origin_country),
            ),
            (
                "runtime",
                lambda episode_run_time: episode_run_time[0] if episode_run_time else 0,
            ),
            (
                "artwork_url_map",  # TODO artwork 应该另外处理？
                lambda poster_path, id: (
                    MediaFileType.POSTER,
                    f"{_ARTWORK_BASE_URL}original{poster_path}",
                ),
            ),
            (
                "production_company",
                lambda networks, production_companies: ", ".join(
                    [n["name"] for n in networks]
                    + [c["name"] for c in production_companies]
                ),
            ),
            (
                "status",
                lambda status: MediaAiredStatus.retrieve_status(status),
            ),
            (
                "year",
                lambda first_air_date: datetime.strptime(
                    first_air_date, "%Y-%m-%d"
                ).year,
            ),
            ("actors", _credits_filter(PersonType.ACTOR)),
            (
                "ids",
                lambda external_ids: ("imdb", external_ids["imdb_id"]),
                Option.KEY_NOT_EXIST_IGNORE_ANY,
            ),
            (
                "ids",
                lambda external_ids: ("tvdb", str(external_ids["tvdb_id"])),
                Option.KEY_NOT_EXIST_IGNORE_ANY,
            ),
            (
                "certification",
                lambda content_ratings, production_countries: self._parse_content_rating(
                    content_ratings, production_countries
                ),
            ),
            ("genres", lambda genres: [_to_genre(g) for g in genres]),
            (
                "genres",
                lambda adult: MediaGenres.EROTIC if adult else [],
                Option.KEY_NOT_EXIST_IGNORE_ANY,
            ),
            (
                "tags",
                lambda keywords: [k["name"] for k in keywords["results"]],
            ),
            ("seasons", ("seasons", season_table)),
        ]

        tvshow = replace(tvshow, tv_context, table)
        return dataclasses.replace(tvshow, episodes=episodes)

    # 按本地化、US、原始发行国的顺序取值
    def _parse_release_date(self, release_dates, production_countries) -> str:
        countries = [self.country, self.fallback_country]
        countries += [
            v["iso_3166_1"]
            for v in production_countries
            if v["iso_3166_1"] not in countries
        ]
        data = _find_release_dates(release_dates, countries)

        for c in countries:
            if c in data:
                items = data[c]
                for item in items:
                    if v := item["release_date"]:
                        return isoparse(v).strftime("%Y-%m-%d")

        return ""

    # 按本地化、US、原始发行国的顺序取值
    def _parse_certification(
        self, release_dates, production_countries
    ) -> MediaCertification:
        countries = [self.country, self.fallback_country]
        countries += [
            v["iso_3166_1"]
            for v in production_countries
            if v["iso_3166_1"] not in countries
        ]
        data = _find_release_dates(release_dates, countries)

        for c in countries:
            if c in data:
                items = data[c]
                for item in items:
                    if cert := item["certification"]:
                        return MediaCertification.retrieve(cert, c)

        return MediaCertification.UNKNOWN

    # 按本地化、US、原始发行国的顺序取值
    def _parse_content_rating(
        self, content_ratings, production_countries
    ) -> MediaCertification:
        countries = [self.country, self.fallback_country]
        countries += [
            v["iso_3166_1"]
            for v in production_countries
            if v["iso_3166_1"] not in countries
        ]
        # FIXME content_rating 与 movie 的 release_dates 结构类似
        data = _find_ratings(content_ratings, countries)

        for c in countries:
            if c in data:
                item = data[c]
                # FIXME 就 key 不一样
                if cert := item["rating"]:
                    return MediaCertification.retrieve(cert, c)

        return MediaCertification.UNKNOWN


def _find_ratings(ratings, countries):
    result = {}
    if ratings and countries:
        release_dates = ratings["results"]
        for data in release_dates:
            if (c := data["iso_3166_1"]) in countries:
                result[c] = data
                if len(result) == len(countries):
                    break

    return result


def _find_release_dates(release_dates, countries):
    result = {}
    release_dates = release_dates["results"]
    for data in release_dates:
        if (c := data["iso_3166_1"]) in countries:
            result[c] = data["release_dates"]
            if len(result) == len(countries):
                break

    return result


def _conv_people(credit, person_type: PersonType):
    return Person(
        persion_type=person_type,
        ids={PROVIDER_ID: credit["id"]},
        name=credit["name"],
        role=credit["character"] if "character" in credit else None,
        thumb_url=f"{_ARTWORK_BASE_URL}h632{credit['profile_path']}"
        if "profile_path" in credit
        else None,
        profile_url=f"{_PROFILE_BASE_URL}{credit['id']}" if "id" in credit else None,
    )


def _crew_filter(person_type: PersonType):
    if person_type is PersonType.DIRECTOR:
        credits_type = "crew"
        filter_ = lambda c: "job" in c and c["job"] == "Director"
    elif person_type is PersonType.WRITER:
        credits_type = "crew"
        filter_ = lambda c: "department" in c and c["department"] == "Writing"
    elif person_type is PersonType.PRODUCER:
        credits_type = "crew"
        filter_ = lambda c: "department" in c and c["department"] == "Production"
    else:
        raise Exception(f"Unkonw PersonType {person_type}")

    def _execute(crew):
        data = crew
        return [_conv_people(c, person_type) for c in data if filter_(c)]

    return _execute


def _credits_filter(person_type: PersonType):
    if person_type is PersonType.ACTOR:
        credits_type = "cast"
        filter_ = lambda c: True
    elif person_type is PersonType.DIRECTOR:
        credits_type = "crew"
        filter_ = lambda c: "job" in c and c["job"] == "Director"
    elif person_type is PersonType.WRITER:
        credits_type = "crew"
        filter_ = lambda c: "department" in c and c["department"] == "Writing"
    elif person_type is PersonType.PRODUCER:
        credits_type = "crew"
        filter_ = lambda c: "department" in c and c["department"] == "Production"
    else:
        raise Exception(f"Unkonw PersonType {person_type}")

    def _execute(credits):
        data = credits[credits_type]
        return [_conv_people(c, person_type) for c in data if filter_(c)]

    return _execute


def _to_genre(tmdb_genre):
    match int(tmdb_genre["id"]):
        case 28 | 10759:
            return MediaGenres.ACTION
        case 12:
            return MediaGenres.ADVENTURE
        case 16:
            return MediaGenres.ANIMATION
        case 35:
            return MediaGenres.COMEDY
        case 80:
            return MediaGenres.CRIME
        case 105:
            return MediaGenres.DISASTER
        case 99:
            return MediaGenres.DOCUMENTARY
        case 18:
            return MediaGenres.DRAMA
        case 82:
            return MediaGenres.EASTERN
        case 2916:
            return MediaGenres.EROTIC
        case 10751:
            return MediaGenres.FAMILY
        case 14:
            return MediaGenres.FANTASY
        case 10753:
            return MediaGenres.FILM_NOIR
        case 10769:
            return MediaGenres.FOREIGN
        case 36:
            return MediaGenres.HISTORY
        case 10595:
            return MediaGenres.HOLIDAY
        case 27:
            return MediaGenres.HORROR
        case 10756:
            return MediaGenres.INDIE
        case 10402:
            return MediaGenres.MUSIC
        case 22:
            return MediaGenres.MUSICAL
        case 9648:
            return MediaGenres.MYSTERY
        case 10754:
            return MediaGenres.NEO_NOIR
        case 10763:
            return MediaGenres.NEWS
        case 10764:
            return MediaGenres.REALITY_TV
        case 1115:
            return MediaGenres.ROAD_MOVIE
        case 10749:
            return MediaGenres.ROMANCE
        case 878 | 10765:
            return MediaGenres.SCIENCE_FICTION
        case 10755:
            return MediaGenres.SHORT
        case 10766:
            return MediaGenres.SOAP
        case 9805:
            return MediaGenres.SPORT
        case 10758:
            return MediaGenres.SPORTING_EVENT
        case 10757:
            return MediaGenres.SPORTS_FILM
        case 10748:
            return MediaGenres.SUSPENSE
        case 10767:
            return MediaGenres.TALK_SHOW
        case 10770:
            return MediaGenres.TV_MOVIE
        case 53:
            return MediaGenres.THRILLER
        case 10752 | 10768:
            return MediaGenres.WAR
        case 37:
            return MediaGenres.WESTERN
        case _:  # 能自动创建枚举外的类型
            return tmdb_genre
