from dataclasses import dataclass

from peets.iso import Country, Language

NAME = "peets"


@dataclass
class Config:
    language: Language = Language.ZH
    country: Country = Country.CN
    tmdb_key: str = "42dd58312a5ca6dd8339b6674e484320"
    include_adult: bool = True
