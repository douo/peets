from typing import Callable

from lxml import etree as ET

from peets.config import Config
from peets.entities import (
    MediaFileType,
    Movie,
    Person,
)
from peets.nfo import Connector, NfoTable, _to_text, create_element

from .common import (
    _actors,
    _country,
    _credits,
    _genre,
    _outline,
    _ratings,
    _studio,
    _tags,
    _thumb,
    _uniqueid_default,
)




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
    return []


def _showlinks(showlinks) -> list[ET._Element]:
    return [create_element("showlink", link) for link in showlinks]


class MovieKodiConnector(Connector[Movie]):
    def __init__(self, config: Config) -> None:
        super().__init__("kodi")
        self.tmdb_key = config.tmdb_key
        self.language = config.language

    @property
    def available_type(self) -> list[str]:
        return ["movie"]

    def _nfo_table(self, _: Movie, belong_to) -> NfoTable:
        return [
            "title",
            ("originaltitle", "original_title"),
            ("sorttitle", "sort_title"),
            ("year", lambda year: year if year != 0 else ""),
            _ratings,
            # "userrating",
            # "votes",
            _set,  # movie_set
            "plot",
            ("outline", _outline),
            "runtime",
            "tagline",
            _thumb,
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
            _uniqueid_default,
            _country,
            ("premiered", "release_date"),  # TODO reconsider date type
            (
                "dateadded",
                lambda date_added: date_added.strftime("%Y-%m-%d %H:%M:%S"),
            ),  # TODO MovieGenericXmlConnector#addDateAdded
            (
                "lockdata",
                lambda: "true",
            ),  # protect the NFO from being modified by Emby
            "watched",
            ("playcount", lambda: 0),  # TODO
            _genre,
            _studio,
            _credits("credits", "writers"),
            _credits("director", "directors"),
            _tags,
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
            "top250",  # TODO
            # TODO status & code
            # TODO fileinfo
        ]
