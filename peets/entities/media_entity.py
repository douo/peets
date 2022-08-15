from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID, uuid4
from datetime import date
from enum import Enum, auto

class MediaFileType(Enum):
  VIDEO = auto()
  TRAILER = auto()
  SAMPLE = auto() #  sample != trailer
  VIDEO_EXTRA = auto()
  AUDIO = auto()
  SUBTITLE = auto()
  NFO = auto()
  POSTER = auto() #  gfx
  FANART = auto() #  gfx
  BANNER = auto() #  gfx
  CLEARART = auto() #  gfx
  DISC = auto() #  gfx
  LOGO = auto() #  gfx
  CLEARLOGO = auto() #  gfx
  THUMB = auto() #  gfx
  CHARACTERART = auto() # gfx
  KEYART = auto() #  gfx
  SEASON_POSTER = auto() #  gfx
  SEASON_FANART = auto() #  gfx
  SEASON_BANNER = auto() #  gfx
  SEASON_THUMB = auto() #  gfx
  EXTRAFANART = auto() #  gfx
  EXTRATHUMB = auto() #  gfx
  EXTRA = auto()
  GRAPHIC = auto() #  NO gfx (since not a searchable type)
  MEDIAINFO = auto() #  xxx-mediainfo.xml
  VSMETA = auto() #  xxx.ext.vsmeta Synology
  THEME = auto() #  "theme" files for some skins = auto()like theme.mp3 (or bg video)
  TEXT = auto() #  various text infos = auto()like BDinfo.txt or others...
  DOUBLE_EXT = auto() #  the filename startsWith video filename (and added extension) = auto()so we keep them...
  UNKNOWN = auto()

@dataclass
class MediaRating:
    rating_id:str = ""
    rating:int = -1
    votes:int = 0
    maxValue:int = 10

@dataclass(kw_only=True)
class MediaEntity:
    dbid:UUID = uuid4()
    locked:bool = False
    dataSource:str = ""
    ids:dict[str, str] = field(default_factory=dict)
    title:str = ""
    original_title:str = ""
    year:int = 0
    plot:str = ""
    path:str = ""
    dateAdded:date = date.today()
    production_company:str = ""
    scraped:bool = False
    note:str = ""
    ratings:dict[str,MediaRating] = field(default_factory=dict)
    media_files:list[str] = field(default_factory=list)
    tags:list[str] = field(default_factory=list)
    artwork_url_map:dict[MediaFileType, str] = field(default_factory=dict)
    original_filename:str = ""
    last_scraper_id:str = ""
    last_scrape_language:str = ""
    newly_added:bool = False
    duplicate:bool = False
