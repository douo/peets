from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import date
from enum import Enum, auto

class CountryCode(Enum):
    """ISO_3166-1 derive from

    https://gitlab.com/tinyMediaManager/tinyMediaManager/-/blob/devel/src/main/java/org/tinymediamanager/scraper/entities/CountryCode.java
    """
    def __init__(self, country, alpha3, numeric) -> None:
        self.country = country
        self.alpha3 = alpha3
        self.numeric = numeric

    AU = ("Australia", "AUS", 36)

    CA = ("Canada", "CAN", 124)

    CH = ("Switzerland", "CHE", 756)

    CN = ("China", "CHN", 156)

    CZ = ("Czech Republic", "CZE", 203)

    DE = ("Germany", "DEU", 276)

    DK = ("Denmark", "DNK", 208)

    EE = ("Estonia", "EST", 233)

    ES = ("Spain", "ESP", 724)

    FI = ("Finland", "FIN", 246)

    FR = ("France", "FRA", 250)

    GB = ("United Kingdom", "GBR", 826)

    GR = ("Greece", "GRC", 300)

    HK = ("Hong Kong", "HKG", 344)

    HU = ("Hungary", "HUN", 348)

    IE = ("Ireland", "IRL", 372)

    IN = ("India", "IND", 356)

    IS = ("Iceland", "ISL", 352)

    IT = ("Italy", "ITA", 380)

    JP = ("Japan", "JPN", 392)

    MX = ("Mexico", "MEX", 484)

    NL = ("Netherlands", "NLD", 528)

    NO = ("Norway", "NOR", 578)

    NZ = ("New Zealand", "NZL", 554)

    PL = ("Poland", "POL", 616)

    PT = ("Portugal", "PRT", 620)

    RO = ("Romania", "ROU", 642)

    RU = ("Russian Federation", "RUS", 643)

    SE = ("Sweden", "SWE", 752)

    TH = ("Thailand", "THA", 764)

    US = ("United States", "USA", 840)

    ZW = ("Zimbabwe", "ZWE", 716)

class MediaCertification(Enum):
    """
    分级

    https://gitlab.com/tinyMediaManager/tinyMediaManager/-/blob/devel/src/main/java/org/tinymediamanager/scraper/entities/MediaCertification.java
    """

    def __init__(self, country:CountryCode, certification: str, possible_notations: list[str]) -> None:
        self.country = country
        self.certifiction = certification
        self.possible_notations = possible_notations

    US_G = (CountryCode.US, "G", [ "G", "Rated G" ])
    US_PG = (CountryCode.US, "PG", [ "PG", "Rated PG" ])
    US_PG13 = (CountryCode.US, "PG-13", [ "PG-13", "Rated PG-13" ])
    US_R = (CountryCode.US, "R", [ "R", "Rated R" ])
    US_NC17 = (CountryCode.US, "NC-17", [ "NC-17", "Rated NC-17" ])

    US_TVY = (CountryCode.US, "TV-Y", [ "TV-Y" ])
    US_TVY7 = (CountryCode.US, "TV-Y7", [ "TV-Y7" ])
    US_TVG = (CountryCode.US, "TV-G", [ "TV-G" ])
    US_TVPG = (CountryCode.US, "TV-PG", [ "TV-PG" ])
    US_TV14 = (CountryCode.US, "TV-14", [ "TV-14" ])
    US_TVMA = (CountryCode.US, "TV-MA", [ "TV-MA" ])

    DE_FSK0 = (CountryCode.DE, "FSK 0", [ "FSK 0", "FSK-0", "FSK0", "0" ])
    DE_FSK6 = (CountryCode.DE, "FSK 6", [ "FSK 6", "FSK-6", "FSK6", "6", "ab 6" ])
    DE_FSK12 = (CountryCode.DE, "FSK 12", [ "FSK 12", "FSK-12", "FSK12", "12", "ab 12" ])
    DE_FSK16 = (CountryCode.DE, "FSK 16", [ "FSK 16", "FSK-16", "FSK16", "16", "ab 16" ])
    DE_FSK18 = (CountryCode.DE, "FSK 18", [ "FSK 18", "FSK-18", "FSK18", "18", "ab 18" ])

    GB_UC = (CountryCode.GB, "UC", [ "UC" ])
    GB_U = (CountryCode.GB, "U", [ "U" ])
    GB_PG = (CountryCode.GB, "PG", [ "PG" ])
    GB_12A = (CountryCode.GB, "12A", [ "12A" ])
    GB_12 = (CountryCode.GB, "12", [ "12" ])
    GB_15 = (CountryCode.GB, "15", [ "15" ])
    GB_18 = (CountryCode.GB, "18", [ "18" ])
    GB_R18 = (CountryCode.GB, "R18", [ "R18" ])
    GB_E = (CountryCode.GB, "E", [ "E" ])

    RU_Y = (CountryCode.RU, "Y", [ "Y" ])
    RU_6 = (CountryCode.RU, "6+", [ "6+" ])
    RU_12 = (CountryCode.RU, "12+", [ "12+" ])
    RU_14 = (CountryCode.RU, "14+", [ "14+" ])
    RU_16 = (CountryCode.RU, "16+", [ "16+" ])
    RU_18 = (CountryCode.RU, "18+", [ "18+" ])

    NL_AL = (CountryCode.NL, "AL", [ "AL" ])
    NL_6 = (CountryCode.NL, "6", [ "6" ])
    NL_9 = (CountryCode.NL, "9", [ "9" ])
    NL_12 = (CountryCode.NL, "12", [ "12" ])
    NL_16 = (CountryCode.NL, "16", [ "16" ])

    JP_G = (CountryCode.JP, "G", [ "G" ])
    JP_PG12 = (CountryCode.JP, "PG-12", [ "PG-12" ])
    JP_R15 = (CountryCode.JP, "R15+", [ "R15+" ])
    JP_R18 = (CountryCode.JP, "R18+", [ "R18+" ])

    IT_T = (CountryCode.IT, "T", [ "T" ])
    IT_VM14 = (CountryCode.IT, "V.M.14", [ "V.M.14", "VM14" ])
    IT_VM18 = (CountryCode.IT, "V.M.18", [ "V.M.18", "VM18" ])

    IN_U = (CountryCode.IN, "U", [ "U" ])
    IN_UA = (CountryCode.IN, "UA", [ "UA" ])
    IN_A = (CountryCode.IN, "A", [ "A" ])
    IN_S = (CountryCode.IN, "S", [ "S" ])

    GR_K = (CountryCode.GR, "K", [ "K" ])
    GR_K13 = (CountryCode.GR, "K-13", [ "K-13", "K13" ])
    GR_K17 = (CountryCode.GR, "K-17", [ "K-17", "K17" ])
    GR_E = (CountryCode.GR, "E", [ "E" ])

    FR_U = (CountryCode.FR, "U", [ "U" ])
    FR_10 = (CountryCode.FR, "10", [ "10" ])
    FR_12 = (CountryCode.FR, "12", [ "12" ])
    FR_16 = (CountryCode.FR, "16", [ "16" ])
    FR_18 = (CountryCode.FR, "18", [ "18" ])

    CA_G = (CountryCode.CA, "G", [ "G" ])
    CA_PG = (CountryCode.CA, "PG", [ "PG" ])
    CA_14A = (CountryCode.CA, "14A", [ "14A" ])
    CA_18A = (CountryCode.CA, "18A", [ "18A" ])
    CA_R = (CountryCode.CA, "R", [ "R" ])
    CA_A = (CountryCode.CA, "A", [ "A" ])

    AU_E = (CountryCode.AU, "E", [ "E" ])
    AU_G = (CountryCode.AU, "G", [ "G" ])
    AU_PG = (CountryCode.AU, "PG", [ "PG" ])
    AU_M = (CountryCode.AU, "M", [ "M" ])
    AU_MA15 = (CountryCode.AU, "MA15+", [ "MA15+" ])
    AU_R18 = (CountryCode.AU, "R18+", [ "R18+" ])
    AU_X18 = (CountryCode.AU, "X18+", [ "X18+" ])
    AU_RC = (CountryCode.AU, "RC", [ "RC" ])

    CZ_U = (CountryCode.CZ, "U", [ "U" ])
    CZ_PG = (CountryCode.CZ, "PG", [ "PG" ])
    CZ_12 = (CountryCode.CZ, "12", [ "12" ])
    CZ_15 = (CountryCode.CZ, "15", [ "15" ])
    CZ_18 = (CountryCode.CZ, "18", [ "18" ])
    CZ_E = (CountryCode.CZ, "E", [ "E" ])

    DK_A = (CountryCode.DK, "A", [ "A" ])
    DK_7 = (CountryCode.DK, "7", [ "7" ])
    DK_11 = (CountryCode.DK, "11", [ "11" ])
    DK_15 = (CountryCode.DK, "15", [ "15" ])
    DK_F = (CountryCode.DK, "F", [ "F" ])

    EE_PERE = (CountryCode.EE, "PERE", [ "PERE" ])
    EE_L = (CountryCode.EE, "L", [ "L" ])
    EE_MS6 = (CountryCode.EE, "MS-6", [ "MS-6" ])
    EE_MS12 = (CountryCode.EE, "MS-12", [ "MS-12" ])
    EE_K12 = (CountryCode.EE, "K-12", [ "K-12" ])
    EE_K14 = (CountryCode.EE, "K-14", [ "K-14" ])
    EE_K16 = (CountryCode.EE, "K-16", [ "K-16" ])

    FI_S = (CountryCode.FI, "S", [ "S" ])
    FI_K7 = (CountryCode.FI, "K-7", [ "K-7" ])
    FI_K12 = (CountryCode.FI, "K-12", [ "K-12" ])
    FI_K16 = (CountryCode.FI, "K-16", [ "K-16" ])
    FI_K18 = (CountryCode.FI, "K-18", [ "K-18" ])
    FI_KE = (CountryCode.FI, "K-E", [ "K-E" ])

    HK_I = (CountryCode.HK, "I", [ "I"])
    HK_II = (CountryCode.HK, "II", [ "II"])
    HK_IIA = (CountryCode.HK, "IIA", [ "IIA"])
    HK_IIB = (CountryCode.HK, "IIB", [ "IIB"])
    HK_III = (CountryCode.HK, "III", [ "III"])

    HU_KN = (CountryCode.HU, "KN", [ "KN" ])
    HU_6 = (CountryCode.HU, "6", [ "6" ])
    HU_12 = (CountryCode.HU, "12", [ "12" ])
    HU_16 = (CountryCode.HU, "16", [ "16" ])
    HU_18 = (CountryCode.HU, "18", [ "18" ])
    HU_X = (CountryCode.HU, "X", [ "X" ])

    IS_L = (CountryCode.IS, "L", [ "L" ])
    IS_7 = (CountryCode.IS, "7", [ "7" ])
    IS_10 = (CountryCode.IS, "10", [ "10" ])
    IS_12 = (CountryCode.IS, "12", [ "12" ])
    IS_14 = (CountryCode.IS, "14", [ "14" ])
    IS_16 = (CountryCode.IS, "16", [ "16" ])
    IS_18 = (CountryCode.IS, "18", [ "18" ])

    IE_G = (CountryCode.IE, "G", [ "G" ])
    IE_PG = (CountryCode.IE, "PG", [ "PG" ])
    IE_12A = (CountryCode.IE, "12A", [ "12A" ])
    IE_15A = (CountryCode.IE, "15A", [ "15A" ])
    IE_16 = (CountryCode.IE, "16", [ "16" ])
    IE_18 = (CountryCode.IE, "18", [ "18" ])

    NZ_G = (CountryCode.NZ, "G", [ "G" ])
    NZ_PG = (CountryCode.NZ, "PG", [ "PG" ])
    NZ_M = (CountryCode.NZ, "M", [ "M" ])
    NZ_R13 = (CountryCode.NZ, "R13", [ "R13" ])
    NZ_R16 = (CountryCode.NZ, "R16", [ "R16" ])
    NZ_R18 = (CountryCode.NZ, "R18", [ "R18" ])
    NZ_R15 = (CountryCode.NZ, "R15", [ "R15" ])
    NZ_RP13 = (CountryCode.NZ, "RP13", [ "RP13" ])
    NZ_RP16 = (CountryCode.NZ, "RP16", [ "RP16" ])
    NZ_R = (CountryCode.NZ, "R", [ "R" ])

    NO_A = (CountryCode.NO, "A", [ "A" ])
    NO_6 = (CountryCode.NO, "6", [ "6" ])
    NO_7 = (CountryCode.NO, "7", [ "7" ])
    NO_9 = (CountryCode.NO, "9", [ "9" ])
    NO_11 = (CountryCode.NO, "11", [ "11" ])
    NO_12 = (CountryCode.NO, "12", [ "12" ])
    NO_15 = (CountryCode.NO, "15", [ "15" ])
    NO_18 = (CountryCode.NO, "18", [ "18" ])

    PL_AL = (CountryCode.PL, "AL", [ "AL" ])
    PL_7 = (CountryCode.PL, "7", [ "7" ])
    PL_12 = (CountryCode.PL, "12", [ "12" ])
    PL_15 = (CountryCode.PL, "15", [ "15" ])
    PL_AP = (CountryCode.PL, "AP", [ "AP" ])
    PL_21 = (CountryCode.PL, "21", [ "21" ])

    RO_AP = (CountryCode.RO, "A.P.", [ "A.P.", "AP" ])
    RO_12 = (CountryCode.RO, "12", [ "12" ])
    RO_15 = (CountryCode.RO, "15", [ "15" ])
    RO_18 = (CountryCode.RO, "18", [ "18" ])
    RO_18X = (CountryCode.RO, "18*", [ "18*" ])

    ES_APTA = (CountryCode.ES, "APTA", [ "APTA" ])
    ES_ER = (CountryCode.ES, "ER", [ "ER" ])
    ES_7 = (CountryCode.ES, "7", [ "7" ])
    ES_12 = (CountryCode.ES, "12", [ "12" ])
    ES_16 = (CountryCode.ES, "16", [ "16" ])
    ES_18 = (CountryCode.ES, "18", [ "18" ])
    ES_PX = (CountryCode.ES, "PX", [ "PX" ])

    SE_BTL = (CountryCode.SE, "BTL", [ "BTL" ])
    SE_7 = (CountryCode.SE, "7", [ "7" ])
    SE_11 = (CountryCode.SE, "11", [ "11" ])
    SE_15 = (CountryCode.SE, "15", [ "15" ])

    CH_0 = (CountryCode.CH, "0", [ "0" ])
    CH_7 = (CountryCode.CH, "7", [ "7" ])
    CH_10 = (CountryCode.CH, "10", [ "10" ])
    CH_12 = (CountryCode.CH, "12", [ "12" ])
    CH_14 = (CountryCode.CH, "14", [ "14" ])
    CH_16 = (CountryCode.CH, "16", [ "16" ])
    CH_18 = (CountryCode.CH, "18", [ "18" ])

    TH_P = (CountryCode.TH, "P", [ "P" ])
    TH_G = (CountryCode.TH, "G", [ "G" ])
    TH_13 = (CountryCode.TH, "13+", [ "13+" ])
    TH_15 = (CountryCode.TH, "15+", [ "15+" ])
    TH_18 = (CountryCode.TH, "18+", [ "18+" ])
    TH_20 = (CountryCode.TH, "20+", [ "20+" ])
    TH_Banned = (CountryCode.TH, "Banned", [ "Banned" ])

    PT_0 = (CountryCode.PT, "Para todos os públicos", [ "Para todos os públicos" ])
    PT_M3 = (CountryCode.PT, "M/3", [ "M/3", "M_3" ])
    PT_M6 = (CountryCode.PT, "M/6", [ "M/6", "M_6" ])
    PT_M12 = (CountryCode.PT, "M/12", [ "M/12", "M_12" ])
    PT_M14 = (CountryCode.PT, "M/14", [ "M/14", "M_14" ])
    PT_M16 = (CountryCode.PT, "M/16", [ "M/16", "M_16" ])
    PT_M18 = (CountryCode.PT, "M/18", [ "M/18", "M_18" ])
    PT_P = (CountryCode.PT, "P", [ "P" ])

    MX_AA = (CountryCode.MX, "AA", [ "MX:AA" ])
    MX_A = (CountryCode.MX, "A", [ "MX:A" ])
    MX_B = (CountryCode.MX, "B", [ "MX:B" ])
    MX_B_15 = (CountryCode.MX, "B-15", [ "MX:B-15" ])
    MX_C = (CountryCode.MX, "C", [ "MX:C" ])
    MX_D = (CountryCode.MX, "D", [ "MX:D" ])

    NOT_RATED = (CountryCode.US, "not rated", [ "not rated", "NR" ])
    UNKNOWN = (None, "unknown", [ "unknown"]);


class MediaGenres(Enum):
    """ Genres from tinyMediaManager

    https://gitlab.com/tinyMediaManager/tinyMediaManager/-/blob/devel/src/main/java/org/tinymediamanager/core/entities/MediaGenres.java
    """
    ACTION = auto()
    ADVENTURE = auto()
    ANIMATION = auto()
    ANIME = auto()
    ANIMAL = auto()
    BIOGRAPHY = auto()
    COMEDY = auto()
    CRIME = auto()
    DISASTER = auto()
    DOCUMENTARY = auto()
    DRAMA = auto()
    EASTERN = auto()
    EROTIC = auto()
    FAMILY = auto()
    FAN_FILM = auto()
    FANTASY = auto()
    FILM_NOIR = auto()
    FOREIGN = auto()
    GAME_SHOW = auto()
    HISTORY = auto()
    HOLIDAY = auto()
    HORROR = auto()
    INDIE = auto()
    MINI_SERIES = auto()
    MUSIC = auto()
    MUSICAL = auto()
    MYSTERY = auto()
    NEO_NOIR = auto()
    NEWS = auto()
    REALITY_TV = auto()
    ROAD_MOVIE = auto()
    ROMANCE = auto()
    SCIENCE_FICTION = auto()
    SERIES = auto()
    SHORT = auto()
    SILENT_MOVIE = auto()
    SOAP = auto()
    SPORT = auto()
    SPORTING_EVENT = auto()
    SPORTS_FILM = auto()
    SUSPENSE = auto()
    TALK_SHOW = auto()
    TV_MOVIE = auto()
    THRILLER = auto()
    WAR = auto()
    WESTERN = auto()


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
    rating_id: str = ""
    rating: int = -1
    votes: int = 0
    max_value: int = 10

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
    artwork_type:MediaArtworkType | None = None
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


@dataclass(kw_only=True)
class MediaEntity:
    dbid: UUID = uuid4()
    locked: bool = False
    data_source: str = ""
    ids: dict[str, str] = field(default_factory=dict)
    title: str = ""
    original_title: str = ""
    year: int = 0
    plot: str = ""
    path: str = ""
    date_added: date = date.today()
    production_company: str = ""
    scraped: bool = False
    note: str = ""
    ratings: dict[str,MediaRating] = field(default_factory=dict)
    media_files: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    artwork_url_map: dict[MediaFileType, str] = field(default_factory=dict)
    original_filename: str = ""
    last_scraper_id: str = ""
    last_scrape_language: str = ""
    newly_added: bool = False
    duplicate: bool = False


@dataclass
class MediaTrailer:
    name:str = ""
    url:str = ""
    quality:str = ""
    provider:str = ""
    in_nfo:bool = False
    date:str = ""


class PersonType(Enum):
    ACTOR = auto(),
    DIRECTOR = auto(),
    WRITER = auto(),
    PRODUCER = auto(),
    OTHER = auto()

@dataclass
class Person:
    persion_type: PersonType = PersonType.OTHER
    name: str = ""
    role: str | None = None
    thumb_url: str | None = None
    profile_url: str | None = None
    ids: dict = field(default_factory=dict)



@dataclass(kw_only=True)
class MovieSet(MediaEntity):
    movie_ids:list[UUID] = field(default_factory=list)
    movies:list["Movie"] = field(default_factory=list)
    title_sortable:str = ""



@dataclass(kw_only=True)
class Movie(MediaEntity):
    sort_title: str = ""
    tagline:str = ""
    runtime:int = 0
    watched:bool = False
    playcount:int = 0
    isDisc:bool = False
    spoken_languages:str = ""
    country:str = ""
    release_date:str = ""
    multi_movie_dir:bool = False # 目录内是否有多个视频文件
    top250:int = 0
    media_source:str = ""  #TODO see guessit.rules.properties.source
    video_in_3d:bool = False
    certification:MediaCertification = MediaCertification.UNKNOWN
    movie_set_id:UUID | None = None
    edition:str = ""  # TODO see guessit.rules.properties.edition
    stacked:bool = False
    offline:bool = False
    genres:list[MediaGenres] = field(default_factory=list)
    extra_thumbs:list[str] = field(default_factory=list)
    extra_fanarts:list[str] =  field(default_factory=list)
    actors:list[Person]  =  field(default_factory=list)
    producers:list[Person]  =  field(default_factory=list)
    directors:list[Person]  =  field(default_factory=list)
    writers:list[Person]  =  field(default_factory=list)
    trailer:list[MediaTrailer] = field(default_factory=list)
    showlinks:list[str] = field(default_factory=list)
    movie_set: MovieSet | None = None
    title_sortable:str = ""
    original_title_sortable = ""
    other_ids = ""
    late_watched:str = "" # date
    localized_spoken_languages:str = ""
