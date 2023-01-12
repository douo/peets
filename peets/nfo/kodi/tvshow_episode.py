from datetime import datetime
from typing import Callable, TypeVar, cast

from lxml import etree as ET

from peets.entities import MediaFileType, Movie, TvShow, TvShowSeason, Person, TvShowEpisode
from peets.nfo import Connector, NfoTable, _to_text, create_element
from peets.config import Config
from .common import _uniqueid, _ratings, _studio, _tags, _credits, _actor


class TvShowEpisodeKodiConnector(Connector[TvShowEpisode]):
    def __init__(self, config: Config) -> None:
        super().__init__("kodi")
        self.tmdb_key = config.tmdb_key
        self.language = config.language

    @property
    def available_type(self) -> list[str]:
        return ["tvshowepisode"]

    def nfo_table(self, media: T) -> NfoTable:
        return [
            "title",
            ("originaltitle", "original_title"),
            # ("showtitle", ),  # TODO: getTvShow().title
            "season",
            "episode",
            ("displayseason", "display_season"),
            ("displayepisode", "display_episode"),
            ("id", lambda ids: ids["tvdb"]),
            _uniqueid,
            _ratings,
            ("userrating", lambda ratings: ""),  # TODO userrating
            # "votes",  # IGNORE
            "plot",
            "runtime",
            (
                "thumb",
                lambda artwork_url_map: artwork_url_map.get(MediaFileType.THUMB),
            ),
            ("mpaa", lambda certification: certification.mpaa()),
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
            _actor,
            # trailer,
            # source,
            # original_filename
            ("user_note", "note")
        ]
