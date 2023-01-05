from datetime import datetime
from typing import Callable

from lxml import etree as ET

from peets.entities import MediaFileType, Movie
from peets.nfo import Connector, NfoTable, create_element, inflate


def _uniqueid(ids: dict) -> list[ET._Element]:
    return [
        create_element("uniqueid", str(v), **{"type": k, "default": str(k == "tmdb")})
        for k, v in ids.items()
    ]


def _country(country) -> list[ET._Element]:
    return [create_element("country", c) for c in country.split(",")]


def _genre(genres) -> list[ET._Element]:
    return [create_element("genre", g.text()) for g in genres]


def _studio(production_company) -> list[ET._Element]:
    return [create_element("studio", c) for c in production_company.split(",")]


def _credits(ele: str, attr: str) -> Callable[[Movie], list[ET._Element]]:
    def _inner(movie: Movie) -> list[ET._Element]:
        result = []
        for p in movie.__getattribute__(attr):
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


class MovieKodiConnector(Connector[Movie]):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    @property
    def available_type(self) -> list[str]:
        return ['movie']

    def generate(self, movie: Movie) -> str:
        root = ET.Element("movie")
        root.addprevious(ET.Comment(f"created on {datetime.now().isoformat()}"))
        doc = ET.ElementTree(root)

        table: NfoTable = [
            "title",
            ("originaltitle", "original_title"),
            ("sorttitle", "sort_title"),
            ("year", lambda year: year if year != 0 else ""),
            (
                "rating",
                lambda ratings: "{:.1f}".format(
                    ratings["tmdb"].rating * 10 / ratings["tmdb"].max_value
                ),
            ),  # FIXME tmdb only
            ("userrating", lambda ratings: ""),  # TODO userrating
            ("votes", lambda ratings: str(ratings["tmdb"].votes)),  # FIXME
            _set,  # movie_set
            "plot",
            ("outline", "plot"),  # FIXME use whole plot
            "tagline",
            "runtime",
            (
                "thumb",
                lambda artwork_url_map: artwork_url_map.get(MediaFileType.POSTER),
            ),
            (
                "fanart",
                lambda artwork_url_map: artwork_url_map.get(MediaFileType.FANART),
            ),
            ("mpaa", lambda certification: certification.mpaa()),
            (
                "certification",
                lambda certification: certification.certification,
            ),
            ("id", lambda ids: ids["imdb"]),
            ("tmdbid", lambda ids: ids["tmdb"]),
            # uniqueid
            _uniqueid,
            # country
            _country,
            ("premiered", "release_date"),  # TODO reconsider date type
            (
                "dateadded",
                lambda date_added: date_added.strftime("%Y-%m-%d %H:%M:%S"),
            ),  # TODO MovieGenericXmlConnector#addDateAdded
            (
                "lockdate",
                lambda: "true",
            ),  # protect the NFO from being modified by Emby
            "watched",
            ("playcount", lambda: 0),  # TODO
            _genre,
            _studio,
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
            ("source", "media_source"),  # TODO
            ("language", "spoken_languages"),  # TODO
            _showlinks,
            # KODI
            "top250",  # TODO
            # TODO status & code
            # TODO fileinfo
        ]

        inflate(root, movie, table)

        return ET.tostring(
            doc,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8",
            standalone=True,
        )
