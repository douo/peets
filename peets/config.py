from __future__ import annotations


from enum import Enum, auto
from dataclasses import dataclass
from pathlib import Path

from peets.iso import Country, Language

NAME = "peets"


class Op(Enum):
    Copy = auto()
    Reflink = auto()
    Move = auto()


@dataclass
class Config:
    language: Language = Language.ZH
    country: Country = Country.CN
    tmdb_key: str = "42dd58312a5ca6dd8339b6674e484320"
    include_adult: bool = True
    naming_template = (
        "{type}/{title} ({year})/{title} ({year}) {screen_size} {audio_codec}"
    )
    media_file_naming_style = "simple"  # simple | follow_video
    op: Op = Op.Reflink

    def merge(self, new: Config | Path):
        pass
