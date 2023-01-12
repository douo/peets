from datetime import datetime
from functools import singledispatchmethod
from typing import Callable, TypeVar, cast

from lxml import etree as ET

from peets.entities import MediaEntity, MediaFileType, Movie, TvShow, TvShowSeason, Person, TvShowEpisode
from peets.nfo import Connector, NfoTable, _to_text, create_element
from peets.config import Config

T = TypeVar("T", Movie, TvShow)


def _uniqueid(ids: dict, default: str = "tmdb") -> list[ET._Element]:
    return [
        create_element("uniqueid", str(v), **{"type": k, "default": str(k == default)})
        for k, v in ids.items()
    ]


def _country(country) -> list[ET._Element]:
    return [create_element("country", c) for c in country.split(",")]


def _genre(genres) -> list[ET._Element]:
    return [create_element("genre", g.text()) for g in genres]


def _studio(production_company) -> list[ET._Element]:
    return [create_element("studio", c) for c in production_company.split(",")]


def _ratings(ratings) -> ET._Element:
    parent = ET.Element("ratings")

    for id_, rating in ratings.items():
        if id_ == "user":
            continue
        r = ET.SubElement(parent, "rating")
        if id_ == "tmdb":
            r.set("name", "themoviedb")
            r.set("default", "true")
        else:
            r.set("name", id_)
            r.set("default", "false")
        r.set("max", _to_text(rating.max_value))
        ET.SubElement(r, "value").text = "{:.1f}".format(rating.rating)
        ET.SubElement(r, "votes").text = _to_text(rating.votes)

    return parent


def _tags(tags) -> list[ET._Element]:
    return [create_element("tag", t) for t in tags]


def _credits(ele: str, attr: str) -> Callable[[MediaEntity], list[ET._Element]]:
    def _inner(entity: MediaEntity) -> list[ET._Element]:
        result = []
        for p in entity.__getattribute__(attr):
            child = ET.Element("credits")
            child.text = p.name
            if "tmdb" in p.ids:
                child.set("tmdbid", str(p.ids["tmdb"]))
            if "imdb" in p.ids:
                child.set("imdbid", str(p.ids["imdb"]))
            if "tvdb" in p.ids:
                child.set("tvdb", str(p.ids["tvdb"]))
            result.append(child)
        return result

    return _inner


def _actor(actors: list[Person]) -> list[ET._Element]:
    result = []
    for p in actors:
        actor = ET.Element("actor")
        name = ET.SubElement(actor, "name")

        name.text = p.name

        if p.role:
            child = ET.SubElement(actor, "role")
            child.text = p.role
        if p.thumb_url:
            child = ET.SubElement(actor, "thumb")
            child.text = p.thumb_url
        if p.profile_url:
            child = ET.SubElement(actor, "profile")
            child.text = p.profile_url

        if "tmdb" in p.ids:
            actor.set("tmdbid", str(p.ids["tmdb"]))
        if "imdb" in p.ids:
            actor.set("imdbid", str(p.ids["imdb"]))
        if "tvdb" in p.ids:
            actor.set("tvdb", str(p.ids["tvdb"]))
        result.append(actor)

    return result





class CommonKodiConnector(Connector[T]):
    def __init__(self, config: Config) -> None:
        super().__init__("kodi")
        self.tmdb_key = config.tmdb_key
        self.language = config.language

    @property
    def available_type(self) -> list[str]:
        return ["movie", "tvshow"]

    @singledispatchmethod
    def nfo_table(self, media: T) -> NfoTable:  # type: ignore[override]
        raise NotImplementedError()

    @nfo_table.register
    def _(self, movie: Movie) -> NfoTable:
        def _actors(ele: str, attr: str) -> Callable[[Movie], list[ET._Element]]:
            def _inner(movie: Movie) -> list[ET._Element]:
                result = []
                for p in movie.__getattribute__(attr):
                    actor = ET.Element(ele)
                    name = ET.SubElement(actor, "name")

                    name.text = p.name

                    if p.role:
                        child = ET.SubElement(actor, "role")
                        child.text = p.role
                    if p.thumb_url:
                        child = ET.SubElement(actor, "thumb")
                        child.text = p.thumb_url
                    if p.profile_url:
                        child = ET.SubElement(actor, "profile")
                        child.text = p.profile_url

                    if "tmdb" in p.ids:
                        actor.set("tmdbid", str(p.ids["tmdb"]))
                    if "imdb" in p.ids:
                        actor.set("imdbid", str(p.ids["imdb"]))
                    if "tvdb" in p.ids:
                        actor.set("tvdb", str(p.ids["tvdb"]))
                    result.append(actor)

                return result

            return _inner

        def _set(movie: Movie) -> list[ET._Element]:
            if ms := movie.movie_set:
                set_ = ET.Element("set")
                name = ET.SubElement(set_, "name")
                name.text = ms.name
                overview = ET.SubElement(set_, "overview")
                overview.text = ms.overview
                collectionId = ET.Element("tmdbCollectionId")
                collectionId.text = str(ms.tmdb_id)
                return [set_, collectionId]

        def _showlinks(showlinks) -> list[ET._Element]:
            return [create_element("showlink", link) for link in showlinks]

        return self.common(movie) + [
            ("sorttitle", "sort_title"),
            (
                "rating",  # TODO copy from tvshow
                lambda ratings: "{:.1f}".format(
                    ratings["tmdb"].rating * 10 / ratings["tmdb"].max_value
                ),
            ),  # FIXME tmdb only
            ("votes", lambda ratings: str(ratings["tmdb"].votes)),  # FIXME
            _set,  # movie_set
            "tagline",
            (
                "thumb",  # TODO copy from tvshow
                lambda artwork_url_map: artwork_url_map.get(MediaFileType.POSTER),
            ),
            (
                "fanart",
                lambda artwork_url_map: artwork_url_map.get(MediaFileType.FANART),
            ),
            _credits("credits", "writers"),
            _credits("director", "directors"),
            _actors("actor", "actors"),
            _actors("producer", "producers"),
            (
                "trailer",
                lambda trailer: next(
                    (t.url for t in trailer if t.in_nfo and t.url.startwith("file")),
                    None,
                ),
            ),
            ("premiered", "release_date"),  # TODO reconsider date type
            ("source", "media_source"),  # TODO
            ("language", "spoken_languages"),  # TODO
            _showlinks,
            "watched",
            # KODI
            "top250",  # TODO
            # TODO status & code
            # TODO fileinfo
        ]

    @nfo_table.register
    def _(self, tvshow: TvShow) -> NfoTable:
        def _thumb(type_: MediaFileType, aspect=None) -> Callable:
            aspect = aspect or type_.name.lower()

            def inner(artwork_url_map: dict[MediaFileType, str]) -> ET._Element | None:
                if url := artwork_url_map.get(type_):
                    return create_element("thumb", url, aspect=aspect)
                return None

            return inner

        def _season_name(seasons: list[TvShowSeason]) -> list[ET._Element]:
            return [
                create_element("namedseason", s.name, number=_to_text(s.season))
                for s in seasons
                if s.name
            ]

        def _season_artwork(type_: MediaFileType) -> Callable:
            def inner(seasons) -> list[ET._Element]:
                return [
                    create_element(
                        "thumb",
                        s.artwork_url_map[type_],
                        aspect=type_.name.lower(),
                        type="season",
                        season=_to_text(s.season),
                    )
                    for s in seasons
                    if type_ in s.artwork_url_map
                ]

            return inner

        def _fanart(artwork_url_map: dict[MediaFileType, str], extra_fanart_urls: list[str]) -> ET._Element | None:
            urls = []
            if url := artwork_url_map.get(MediaFileType.FANART):
                urls.append(url)
            urls += extra_fanart_urls

            if urls:
                parent = create_element("fanart")
                for url in urls:
                    thumb = ET.SubElement(parent)
                    thumb.text = url

                return parent

            return None

        def _episodeguide(key: str) -> ET._Element:
            # FIXME tmdb only
            def inner(ids: dict):
                parent = create_element("episodeguide")
                url = create_element(
                    "url",
                    f"http://api.themoviedb.org/3/tv/{_to_text(ids['tmdb'])}?api_key={key}&language={self.language.name.lower()}",
                )
                parent.append(url)
                return parent

            return inner


        def _watched(episodes: list[TvShowEpisode]) -> bool:
            found = False
            for e in episodes:
                if not e.dummy:
                    found = True
                    if not e.watched:
                        return False

            return found

        return self.common(tvshow) + [
            ("showtitle", "title"),
            _ratings,
            ("premiered", "first_aired"),  # TODO reconsider date type
            # "outline",
            # "tagline",
            _thumb(MediaFileType.POSTER),
            _thumb(MediaFileType.BANNER),
            _thumb(MediaFileType.CLEARART),
            _thumb(MediaFileType.CLEARLOGO),
            _thumb(MediaFileType.THUMB),
            _thumb(MediaFileType.KEYART),
            _thumb(MediaFileType.LOGO),
            _thumb(MediaFileType.CHARACTERART),
            _thumb(MediaFileType.DISC, "discart"),
            _season_name,
            _season_artwork(MediaFileType.POSTER),
            _season_artwork(MediaFileType.BANNER),
            _season_artwork(MediaFileType.THUMB),
            _fanart,
            _episodeguide(self.tmdb_key),
            ("status", lambda status: status.name_),
            _tags,
            _actor,
            ("watched", _watched),
            # _trailer, TODO
            ("user_note", "note"),
        ]

    def common(self, media: T) -> NfoTable:
        return [
            "title",
            ("originaltitle", "original_title"),
            ("sorttitle", "sort_title"),
            ("year", lambda year: year if year != 0 else ""),
            ("userrating", lambda ratings: ""),  # TODO userrating
            "plot",
            ("outline", "plot"),  # FIXME use whole plot
            "runtime",
            ("mpaa", lambda certification: certification.mpaa()),
            (
                "certification",
                lambda certification: certification.certification,
            ),
            ("id", lambda ids: ids["imdb"]),
            ("tmdbid", lambda ids: ids["tmdb"]),
            _uniqueid,
            _country,
            (
                "dateadded",
                lambda date_added: date_added.strftime("%Y-%m-%d %H:%M:%S"),
            ),  # TODO MovieGenericXmlConnector#addDateAdded
            (
                "lockdata",
                lambda: "true",
            ),  # protect the NFO from being modified by Emby
            ("playcount", lambda: 0),  # TODO
            _genre,
            _studio,
            (
                "trailer",
                lambda trailer: next(
                    (t.url for t in trailer if t.in_nfo and t.url.startwith("file")),
                    None,
                ),
            ),
        ]
