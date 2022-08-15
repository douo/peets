from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID, uuid4
from datetime import date
from enum import Enum, auto

class MediaArtworkType(Enum):
    """
    The different types of artwork we know
    """
    BACKGROUND = auto()
    BANNER = auto()
    POSTER = auto()
    ACTOR = auto()
    SEASON_POSTER = auto()
    SEASON_FANART = auto()
    SEASON_BANNER = auto()
    SEASON_THUMB = auto()
    THUMB = auto()
    CLEARART = auto()
    KEYART = auto()
    CHARACTERART = auto()
    DISC = auto()
    LOGO = auto()
    CLEARLOGO = auto()
    ALL = auto()

class PosterSizes(Enum):
    """
     All available poster sizes
    """

    def __init__(self, text:str, order:int) -> None:
        self.text = text
        self.order = order


    XLARGE = ("xlarge" + ": ~2000x3000px", 16)
    LARGE = ("large" + ": ~1000x1500px", 8)
    BIG = ("big" + ": ~500x750px", 4)
    MEDIUM = ("medium" + ": ~342x513px", 2)
    SMALL= ("small" + ": ~185x277px", 1)

class FanartSizes(Enum):
    """
    All available fanart sizes
    """
    def __init__(self, text:str, order:int) -> None:
        self.text = text
        self.order = order


    XLARGE = ("xlarge" + ": ~3840x2160px", 16)
    LARGE = ("large" + ": ~1920x1080px", 8)
    MEDIUM = ("medium" + ": ~1280x720px", 2)
    SMALL= ("small" + ": ~300x168px", 1)

@dataclass
class ImageSizeAndUrl:
    width:int
    height:int
    url:str

@dataclass
class MediaArtwork:
    provider_id:str = ""
    artwork_type:Optional[MediaArtworkType] = None
    imdbId:str = ""
    tmdbId:int = 0
    season:int = -1
    preview_url:str = ""
    default_url:str = ""
    original_url:str = ""
    language:str = ""
    size_order:int = 0
    likes:int = 0
    animated:bool = False
    image_sizes:list[ImageSizeAndUrl] = field(default_factory=list)
