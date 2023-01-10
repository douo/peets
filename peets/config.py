from dataclasses import dataclass

from peets.iso import Country, Language


NAME = "peets"


@dataclass
class Config:
    lang: Language = Language.ZH
    country: Country = Country.CN
