from datetime import datetime
from functools import partial, singledispatchmethod
from typing import Callable, TypeVar, cast

from lxml import etree as ET

from peets.config import Config
from peets.entities import (
    MediaFileType,
    Movie,
    Person,
    TvShow,
    TvShowEpisode,
    TvShowSeason,
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


def _fanart(
    artwork_url_map: dict[MediaFileType, str], extra_fanart_urls: list[str]
) -> ET._Element | None:
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


def _episodeguide(config) -> ET._Element:
    # FIXME tmdb only
    def inner(ids: dict):
        parent = create_element("episodeguide")
        url = create_element(
            "url",
            f"http://api.themoviedb.org/3/tv/{_to_text(ids['tmdb'])}?api_key={config.tmdb_key}&language={config.language.name.lower()}",
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


class TvShowKodiConnector(Connector[TvShow]):
    def __init__(self, config: Config) -> None:
        super().__init__("kodi")
        self.tmdb_key = config.tmdb_key
        self.language = config.language

    @property
    def available_type(self) -> list[str]:
        return ["tvshow"]

    def _nfo_table(self, _: TvShow, belong_to) -> NfoTable:  # type: ignore[override]
        return [
            "title",
            ("originaltitle", "original_title"),
            ("showtitle", "title"),
            ("sorttitle", "sort_title"),
            ("year", lambda year: year if year != 0 else ""),
            _ratings,
            # "userrating",
            # "votes",
            "plot",
            ("outline", _outline),  # FIXME use whole plot
            "runtime",
            _thumb,
            _season_name,
            _season_artwork(MediaFileType.POSTER),
            _season_artwork(MediaFileType.BANNER),
            _season_artwork(MediaFileType.THUMB),
            _fanart,
            ("mpaa", lambda certification: certification.mpaa()),
            (
                "certification",
                lambda certification: certification.certification,
            ),
            _episodeguide(self),
            ("id", lambda ids: ids.get("tvdb")),
            ("imdbid", lambda ids: ids["imdb"]),
            ("tmdbid", lambda ids: ids["tmdb"]),
            _uniqueid_default,
            ("premiered", "first_aired"),  # TODO reconsider date type
            (
                "dateadded",
                lambda date_added: date_added.strftime("%Y-%m-%d %H:%M:%S"),
            ),  # TODO MovieGenericXmlConnector#addDateAdded
            (
                "lockdata",
                lambda: "true",
            ),  # protect the NFO from being modified by Emby
            ("status", lambda status: status.name_),
            ("watched", _watched),
            ("playcount", lambda: 0),  # TODO
            _genre,
            _studio,
            _country,
            _tags,
            _actors("actor", "actors"),
            (
                "trailer",
                lambda trailer: next(
                    (t.url for t in trailer if t.in_nfo and t.url.startwith("file")),
                    None,
                ),
            ),
            _tags,
            ("user_note", "note"),
        ]
