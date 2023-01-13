from datetime import datetime
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

from .common import _actors, _credits, _ratings, _studio, _tags, _uniqueid


class TvShowEpisodeKodiConnector(Connector[TvShowEpisode]):
    def __init__(self, config: Config) -> None:
        super().__init__("kodi")
        self.tmdb_key = config.tmdb_key
        self.language = config.language

    @property
    def available_type(self) -> list[str]:
        return ["tvshowepisode"]

    def _get_root_name(self, _) -> str:
        return "episodedetails"

    def _nfo_table(self, _: TvShowEpisode) -> NfoTable:
        return [
            "title",
            ("originaltitle", "original_title"),
            # ("showtitle", ),  # TODO: getTvShow().title
            "season",
            "episode",
            ("displayseason", "display_season"),
            ("displayepisode", "display_episode"),
            ("id", lambda ids: ids.get("tvdb")),
            _uniqueid("imdb"),
            _ratings,
            ("userrating", lambda ratings: ""),  # TODO userrating
            # "votes",  # IGNORE
            "plot",
            # "runtime",  #TODO tvshow.runtime
            (
                "thumb",
                lambda artwork_url_map: artwork_url_map.get(MediaFileType.THUMB),
            ),
            ("mpaa", lambda: ""),
            ("premiered", "first_aired"),
            (
                "dateadded",
                lambda date_added: date_added.strftime("%Y-%m-%d %H:%M:%S"),
            ),
            (
                "lockdata",
                lambda: "true",
            ),
            ("aired", "first_aired"),
            "watched",
            ("playcount", lambda: 0),  # TODO
            # lastplayed
            _studio,
            _tags,
            _credits("credits", "writers"),
            _credits("director", "directors"),
            _actors("actor", "actors"),
            # trailer,
            # source,
            # original_filename
            ("user_note", "note"),
        ]
