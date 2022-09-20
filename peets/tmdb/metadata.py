from __future__ import annotations
from abc import ABC
from datetime import datetime
from dateutil.parser import isoparse
from typing_extensions import TypeAlias
from tmdbsimple.movies import Movies
from peets.entities import MediaCertification, MediaEntity, Movie, MediaFileType, MediaRating, MediaGenres, MediaArtwork, MediaArtworkType, MovieSet, Person, PersonType
from peets.merger import replace
from peets.iso import Language, Country
from peets.scraper import Feature, MetadataProvider, Provider, SearchResult
import tmdbsimple as tmdb
from .config import PROVIDER_ID, _ARTWORK_BASE_URL, _PROFILE_BASE_URL

class TmdbMovieMetadata(MetadataProvider[Movie]):
    def __init__(self,
                 language: Language,
                 country: Country,
                 include_adult: bool = True,
                 ) -> None:
        super().__init__()

        self.language = f"{language.name}-{country.name}".lower()
        self.country =  country.name
        self.include_adult = include_adult

        self.fallback_country = Country.US.name
        self.fallback_lan = "en-us"

    def available_type(self) -> list[str]:
        return ["movie"]

    def search(self, movie: Movie) -> list[SearchResult]:
        api = tmdb.Search()
        resp = api.movie(
            language=self.language,
            query = movie.title,
            include_adult = self.include_adult,
            year = movie.year,
        )
        return api.results

    def apply(self, movie: Movie, **kwargs) -> Movie:
        m_id = kwargs['id_']
        api = tmdb.Movies(m_id)
        context = api.info(
            language=self.language,
            append_to_response="credits,keywords,release_dates,translations"
        )

        table = [
            ("imdb_id","ids", lambda id_: ("imdb", str(id_))), # dict 类型的返回 (key value)
            ("id","ids", lambda id_: (PROVIDER_ID, str(id_))),
            ("overview", "plot"),
            (("vote_average", "vote_count"),
             "ratings",
             lambda va, vc : (PROVIDER_ID, MediaRating(rating_id = "tmdb", rating=va, votes=vc))
             ),
            (("poster_path", "id"), "artwork_url_map",  #TODO artwork 应该另外处理？
             lambda path, id_: (MediaFileType.POSTER, f"{_ARTWORK_BASE_URL}original{path}")
             # MediaArtwork(
             #     provider_id=PROVIDER_ID,
             #     artwork_type=MediaArtworkType.POSTER,
             #     preview_url=f"{artwork_base_url}w342{path}",
             #     default_url=f"{artwork_base_url}original{path}",
             #     original_url=f"{artwork_base_url}original{path}",
             #     language=language,
             #     tmdbId=id_
             ), # 列表类型，返回单项表示插入？？
            ("spoken_languages","spoken_languages",
             lambda spoken_languages: ", ".join([lang["iso_639_1"] for lang in spoken_languages])),
            ("production_countries", "country",
             lambda production_countries: ", ".join([country["iso_3166_1"] for country in production_countries])),
            ("production_companies", "production_company",
             lambda production_companies: ", ".join([company["name"] for company in production_companies])),
            # 一对多的情况下，支持通过 tuple 指定
            # 转换函数表示默认赋值
            ("release_date", "year", lambda release_date: datetime.strptime(release_date, "%Y-%m-%d").year),
            ("release_dates", "release_date", lambda release_dates: self._parse_release_date(release_dates)),
            ("release_dates", "certification", lambda release_dates: self._parse_certification(release_dates)),
            #credits TODO partition
            ("credits", ("actors", "producers", "directors", "writers"),
             (_credits_filter(PersonType.ACTOR), _credits_filter(PersonType.PRODUCER), _credits_filter(PersonType.DIRECTOR), _credits_filter(PersonType.WRITER))),
            #genres
            ("genres", "genres", lambda genres: [_to_genre(g) for g in genres]),
            ("adult", "genres", lambda adult: MediaGenres.EROTIC if adult else []),
            ("belongs_to_collection", "movie_set", lambda data: MovieSet(name = data["name"], tmdb_id = data["id"]) if data else None),
            ("keywords", "tags", lambda keywords: [k["name"] for k in keywords["keywords"]])
        ]

        return replace(movie, context, table)


    def _find_release_dates(self, release_dates):
        fallback = None
        target = None
        release_dates = release_dates["results"]
        for data in release_dates:
            if data["iso_3166_1"] == self.country:
                target = data
            elif data["iso_3166_1"] == self.fallback_country:
                fallback = data
            if target and fallback:
                break

        return fallback,target

    def _parse_release_date(self, release_dates) -> str:
        fallback, data = self._find_release_dates(release_dates)
        result = None
        if data:
            data = data["release_dates"][0]
            if data:
                result =  isoparse(data["release_date"]).strftime("%Y-%m-%d")
        if not result and fallback:
            # breakpoint()
            data = fallback["release_dates"][0]
            if data:
                result =  isoparse(data["release_date"]).strftime("%Y-%m-%d")
        return result or ""


    def _parse_certification(self, release_dates) -> MediaCertification:
        fallback, data = self._find_release_dates(release_dates)
        result = None
        if data:
            country = data["iso_3166_1"]
            cert = data["release_dates"][0]["certification"]
            try:
                result = next(v for _, v in MediaCertification.__members__.items()
                              if v.country and v.country.name == country and cert in v.possible_notations
                              )
            except StopIteration:
                pass
        if not result and fallback:
            country = fallback["iso_3166_1"]
            cert = fallback["release_dates"][0]["certification"]
            try:
                result = next(v for _, v in MediaCertification.__members__.items()
                              if v.country and v.country.name == country and cert in v.possible_notations
                              )
            except StopIteration:
                pass

        return result or MediaCertification.UNKNOWN

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

    def _conv(credit):
        return Person(
            persion_type= person_type,
            ids={PROVIDER_ID: credit["id"]},
            name= credit["name"],
            role= credit["character"] if "character" in credit else None,
            thumb_url=f"{_ARTWORK_BASE_URL}h632{credit['profile_path']}" if "profile_path" in credit else None,
            profile_url=f"{_PROFILE_BASE_URL}{credit['id']}" if "id" in credit else None
        )
    def _execute(credits):
        data = credits[credits_type]
        return [_conv(c) for c in data if filter_(c)]

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
        case _: # 能自动创建枚举外的类型
            return tmdb_genre
