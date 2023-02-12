from __future__ import annotations

import json
from dataclasses import dataclass, field, is_dataclass, asdict
from datetime import datetime, date
from enum import Enum, auto
from pathlib import Path
from typing import TypeAlias, Iterator, Any
from uuid import UUID, uuid4
from itertools import groupby
from operator import attrgetter

from peets.iso import Country


class EntityJsonEncoder(json.JSONEncoder):
    def default(self, o):
        print(f"default {o=}")
        if is_dataclass(o):
            # fix json module: TypeError: keys must be str, int, float, bool or None, not XXX
            def _sanitize(o):
                if isinstance(o, dict):
                    return {_sanitize(k): v for k, v in o.items()}
                elif isinstance(o, Enum):
                    return o.name
                else:
                    return o
            return {k: _sanitize(v) for k, v in  asdict(o).items()}
        elif isinstance(o, Enum):
            return o.name
        elif isinstance(o, Path):
            return str(Path)
        elif isinstance(o, UUID):
            return str(o)
        elif isinstance(o, (datetime, date)):
            return o.isoformat()
        else:
            return super().default(o)



class MediaCertification(Enum):
    """
    分级

    https://gitlab.com/tinyMediaManager/tinyMediaManager/-/blob/devel/src/main/java/org/tinymediamanager/scraper/entities/MediaCertification.java
    """

    def __init__(
        self, country: Country, certification: str, possible_notations: list[str]
    ) -> None:
        self.country = country
        self.certification = certification
        self.possible_notations = possible_notations

    def mpaa(self) -> str:
        match self:
            case MediaCertification.US_G:
                return "Rated G"
            case MediaCertification.US_PG:
                return "Rated PG"
            case MediaCertification.US_PG13:
                return "Rated PG-13"
            case MediaCertification.US_R:
                return "Rated R"
            case MediaCertification.US_NC17:
                return "Rated NC-17"
            case MediaCertification.NOT_RATED:
                return "NR"
            # TV shows
            case (
                MediaCertification.US_TVY7
                | MediaCertification.US_TV14
                | MediaCertification.US_TVPG
                | MediaCertification.US_TVMA
                | MediaCertification.US_TVG
                | MediaCertification.US_TVY
            ) as cert:
                return cert.certification
            case _:
                return ""

    @classmethod
    def retrieve(cls, cert: str, country: str) -> MediaCertification:
        members = cls.__members__
        for m in members.values():
            if (
                m.country.name.lower() == country.lower()
                and cert in m.possible_notations
            ):
                return m
        return MediaCertification.UNKNOWN

    US_G = (Country.US, "G", ["G", "Rated G"])
    US_PG = (Country.US, "PG", ["PG", "Rated PG"])
    US_PG13 = (Country.US, "PG-13", ["PG-13", "Rated PG-13"])
    US_R = (Country.US, "R", ["R", "Rated R"])
    US_NC17 = (Country.US, "NC-17", ["NC-17", "Rated NC-17"])

    US_TVY = (Country.US, "TV-Y", ["TV-Y"])
    US_TVY7 = (Country.US, "TV-Y7", ["TV-Y7"])
    US_TVG = (Country.US, "TV-G", ["TV-G"])
    US_TVPG = (Country.US, "TV-PG", ["TV-PG"])
    US_TV14 = (Country.US, "TV-14", ["TV-14"])
    US_TVMA = (Country.US, "TV-MA", ["TV-MA"])

    DE_FSK0 = (Country.DE, "FSK 0", ["FSK 0", "FSK-0", "FSK0", "0"])
    DE_FSK6 = (Country.DE, "FSK 6", ["FSK 6", "FSK-6", "FSK6", "6", "ab 6"])
    DE_FSK12 = (Country.DE, "FSK 12", ["FSK 12", "FSK-12", "FSK12", "12", "ab 12"])
    DE_FSK16 = (Country.DE, "FSK 16", ["FSK 16", "FSK-16", "FSK16", "16", "ab 16"])
    DE_FSK18 = (Country.DE, "FSK 18", ["FSK 18", "FSK-18", "FSK18", "18", "ab 18"])

    GB_UC = (Country.GB, "UC", ["UC"])
    GB_U = (Country.GB, "U", ["U"])
    GB_PG = (Country.GB, "PG", ["PG"])
    GB_12A = (Country.GB, "12A", ["12A"])
    GB_12 = (Country.GB, "12", ["12"])
    GB_15 = (Country.GB, "15", ["15"])
    GB_18 = (Country.GB, "18", ["18"])
    GB_R18 = (Country.GB, "R18", ["R18"])
    GB_E = (Country.GB, "E", ["E"])

    RU_Y = (Country.RU, "Y", ["Y"])
    RU_6 = (Country.RU, "6+", ["6+"])
    RU_12 = (Country.RU, "12+", ["12+"])
    RU_14 = (Country.RU, "14+", ["14+"])
    RU_16 = (Country.RU, "16+", ["16+"])
    RU_18 = (Country.RU, "18+", ["18+"])

    NL_AL = (Country.NL, "AL", ["AL"])
    NL_6 = (Country.NL, "6", ["6"])
    NL_9 = (Country.NL, "9", ["9"])
    NL_12 = (Country.NL, "12", ["12"])
    NL_16 = (Country.NL, "16", ["16"])

    JP_G = (Country.JP, "G", ["G"])
    JP_PG12 = (Country.JP, "PG-12", ["PG-12"])
    JP_R15 = (Country.JP, "R15+", ["R15+"])
    JP_R18 = (Country.JP, "R18+", ["R18+"])

    IT_T = (Country.IT, "T", ["T"])
    IT_VM14 = (Country.IT, "V.M.14", ["V.M.14", "VM14"])
    IT_VM18 = (Country.IT, "V.M.18", ["V.M.18", "VM18"])

    IN_U = (Country.IN, "U", ["U"])
    IN_UA = (Country.IN, "UA", ["UA"])
    IN_A = (Country.IN, "A", ["A"])
    IN_S = (Country.IN, "S", ["S"])

    GR_K = (Country.GR, "K", ["K"])
    GR_K13 = (Country.GR, "K-13", ["K-13", "K13"])
    GR_K17 = (Country.GR, "K-17", ["K-17", "K17"])
    GR_E = (Country.GR, "E", ["E"])

    FR_U = (Country.FR, "U", ["U"])
    FR_10 = (Country.FR, "10", ["10"])
    FR_12 = (Country.FR, "12", ["12"])
    FR_16 = (Country.FR, "16", ["16"])
    FR_18 = (Country.FR, "18", ["18"])

    CA_G = (Country.CA, "G", ["G"])
    CA_PG = (Country.CA, "PG", ["PG"])
    CA_14A = (Country.CA, "14A", ["14A"])
    CA_18A = (Country.CA, "18A", ["18A"])
    CA_R = (Country.CA, "R", ["R"])
    CA_A = (Country.CA, "A", ["A"])

    AU_E = (Country.AU, "E", ["E"])
    AU_G = (Country.AU, "G", ["G"])
    AU_PG = (Country.AU, "PG", ["PG"])
    AU_M = (Country.AU, "M", ["M"])
    AU_MA15 = (Country.AU, "MA15+", ["MA15+"])
    AU_R18 = (Country.AU, "R18+", ["R18+"])
    AU_X18 = (Country.AU, "X18+", ["X18+"])
    AU_RC = (Country.AU, "RC", ["RC"])

    CZ_U = (Country.CZ, "U", ["U"])
    CZ_PG = (Country.CZ, "PG", ["PG"])
    CZ_12 = (Country.CZ, "12", ["12"])
    CZ_15 = (Country.CZ, "15", ["15"])
    CZ_18 = (Country.CZ, "18", ["18"])
    CZ_E = (Country.CZ, "E", ["E"])

    DK_A = (Country.DK, "A", ["A"])
    DK_7 = (Country.DK, "7", ["7"])
    DK_11 = (Country.DK, "11", ["11"])
    DK_15 = (Country.DK, "15", ["15"])
    DK_F = (Country.DK, "F", ["F"])

    EE_PERE = (Country.EE, "PERE", ["PERE"])
    EE_L = (Country.EE, "L", ["L"])
    EE_MS6 = (Country.EE, "MS-6", ["MS-6"])
    EE_MS12 = (Country.EE, "MS-12", ["MS-12"])
    EE_K12 = (Country.EE, "K-12", ["K-12"])
    EE_K14 = (Country.EE, "K-14", ["K-14"])
    EE_K16 = (Country.EE, "K-16", ["K-16"])

    FI_S = (Country.FI, "S", ["S"])
    FI_K7 = (Country.FI, "K-7", ["K-7"])
    FI_K12 = (Country.FI, "K-12", ["K-12"])
    FI_K16 = (Country.FI, "K-16", ["K-16"])
    FI_K18 = (Country.FI, "K-18", ["K-18"])
    FI_KE = (Country.FI, "K-E", ["K-E"])

    HK_I = (Country.HK, "I", ["I"])
    HK_II = (Country.HK, "II", ["II"])
    HK_IIA = (Country.HK, "IIA", ["IIA"])
    HK_IIB = (Country.HK, "IIB", ["IIB"])
    HK_III = (Country.HK, "III", ["III"])

    HU_KN = (Country.HU, "KN", ["KN"])
    HU_6 = (Country.HU, "6", ["6"])
    HU_12 = (Country.HU, "12", ["12"])
    HU_16 = (Country.HU, "16", ["16"])
    HU_18 = (Country.HU, "18", ["18"])
    HU_X = (Country.HU, "X", ["X"])

    IS_L = (Country.IS, "L", ["L"])
    IS_7 = (Country.IS, "7", ["7"])
    IS_10 = (Country.IS, "10", ["10"])
    IS_12 = (Country.IS, "12", ["12"])
    IS_14 = (Country.IS, "14", ["14"])
    IS_16 = (Country.IS, "16", ["16"])
    IS_18 = (Country.IS, "18", ["18"])

    IE_G = (Country.IE, "G", ["G"])
    IE_PG = (Country.IE, "PG", ["PG"])
    IE_12A = (Country.IE, "12A", ["12A"])
    IE_15A = (Country.IE, "15A", ["15A"])
    IE_16 = (Country.IE, "16", ["16"])
    IE_18 = (Country.IE, "18", ["18"])

    NZ_G = (Country.NZ, "G", ["G"])
    NZ_PG = (Country.NZ, "PG", ["PG"])
    NZ_M = (Country.NZ, "M", ["M"])
    NZ_R13 = (Country.NZ, "R13", ["R13"])
    NZ_R16 = (Country.NZ, "R16", ["R16"])
    NZ_R18 = (Country.NZ, "R18", ["R18"])
    NZ_R15 = (Country.NZ, "R15", ["R15"])
    NZ_RP13 = (Country.NZ, "RP13", ["RP13"])
    NZ_RP16 = (Country.NZ, "RP16", ["RP16"])
    NZ_R = (Country.NZ, "R", ["R"])

    NO_A = (Country.NO, "A", ["A"])
    NO_6 = (Country.NO, "6", ["6"])
    NO_7 = (Country.NO, "7", ["7"])
    NO_9 = (Country.NO, "9", ["9"])
    NO_11 = (Country.NO, "11", ["11"])
    NO_12 = (Country.NO, "12", ["12"])
    NO_15 = (Country.NO, "15", ["15"])
    NO_18 = (Country.NO, "18", ["18"])

    PL_AL = (Country.PL, "AL", ["AL"])
    PL_7 = (Country.PL, "7", ["7"])
    PL_12 = (Country.PL, "12", ["12"])
    PL_15 = (Country.PL, "15", ["15"])
    PL_AP = (Country.PL, "AP", ["AP"])
    PL_21 = (Country.PL, "21", ["21"])

    RO_AP = (Country.RO, "A.P.", ["A.P.", "AP"])
    RO_12 = (Country.RO, "12", ["12"])
    RO_15 = (Country.RO, "15", ["15"])
    RO_18 = (Country.RO, "18", ["18"])
    RO_18X = (Country.RO, "18*", ["18*"])

    ES_APTA = (Country.ES, "APTA", ["APTA"])
    ES_ER = (Country.ES, "ER", ["ER"])
    ES_7 = (Country.ES, "7", ["7"])
    ES_12 = (Country.ES, "12", ["12"])
    ES_16 = (Country.ES, "16", ["16"])
    ES_18 = (Country.ES, "18", ["18"])
    ES_PX = (Country.ES, "PX", ["PX"])

    SE_BTL = (Country.SE, "BTL", ["BTL"])
    SE_7 = (Country.SE, "7", ["7"])
    SE_11 = (Country.SE, "11", ["11"])
    SE_15 = (Country.SE, "15", ["15"])

    CH_0 = (Country.CH, "0", ["0"])
    CH_7 = (Country.CH, "7", ["7"])
    CH_10 = (Country.CH, "10", ["10"])
    CH_12 = (Country.CH, "12", ["12"])
    CH_14 = (Country.CH, "14", ["14"])
    CH_16 = (Country.CH, "16", ["16"])
    CH_18 = (Country.CH, "18", ["18"])

    TH_P = (Country.TH, "P", ["P"])
    TH_G = (Country.TH, "G", ["G"])
    TH_13 = (Country.TH, "13+", ["13+"])
    TH_15 = (Country.TH, "15+", ["15+"])
    TH_18 = (Country.TH, "18+", ["18+"])
    TH_20 = (Country.TH, "20+", ["20+"])
    TH_Banned = (Country.TH, "Banned", ["Banned"])

    PT_0 = (Country.PT, "Para todos os públicos", ["Para todos os públicos"])
    PT_M3 = (Country.PT, "M/3", ["M/3", "M_3"])
    PT_M6 = (Country.PT, "M/6", ["M/6", "M_6"])
    PT_M12 = (Country.PT, "M/12", ["M/12", "M_12"])
    PT_M14 = (Country.PT, "M/14", ["M/14", "M_14"])
    PT_M16 = (Country.PT, "M/16", ["M/16", "M_16"])
    PT_M18 = (Country.PT, "M/18", ["M/18", "M_18"])
    PT_P = (Country.PT, "P", ["P"])

    MX_AA = (Country.MX, "AA", ["MX:AA"])
    MX_A = (Country.MX, "A", ["MX:A"])
    MX_B = (Country.MX, "B", ["MX:B"])
    MX_B_15 = (Country.MX, "B-15", ["MX:B-15"])
    MX_C = (Country.MX, "C", ["MX:C"])
    MX_D = (Country.MX, "D", ["MX:D"])

    NOT_RATED = (Country.US, "not rated", ["not rated", "NR"])
    UNKNOWN = (None, "unknown", ["unknown"])


class MediaGenres(Enum):
    """Genres from tinyMediaManager

    https://gitlab.com/tinyMediaManager/tinyMediaManager/-/blob/devel/src/main/java/org/tinymediamanager/core/entities/MediaGenres.java
    """

    def text(self) -> str:
        return self.name.title().replace("_", " ")

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
    SAMPLE = auto()  # sample != trailer
    VIDEO_EXTRA = auto()
    AUDIO = auto()
    SUBTITLE = auto()
    NFO = auto()
    POSTER = auto()  # gfx
    FANART = auto()  # gfx
    BANNER = auto()  # gfx
    CLEARART = auto()  # gfx
    DISC = auto()  # gfx
    LOGO = auto()  # gfx
    CLEARLOGO = auto()  # gfx
    THUMB = auto()  # gfx
    CHARACTERART = auto()  # gfx
    KEYART = auto()  # gfx
    SEASON_POSTER = auto()  # gfx
    SEASON_FANART = auto()  # gfx
    SEASON_BANNER = auto()  # gfx
    SEASON_THUMB = auto()  # gfx
    EXTRAFANART = auto()  # gfx
    EXTRATHUMB = auto()  # gfx
    EXTRA = auto()
    GRAPHIC = auto()  # NO gfx (since not a searchable type)
    MEDIAINFO = auto()  # xxx-mediainfo.xml
    VSMETA = auto()  # xxx.ext.vsmeta Synology
    THEME = auto()  # "theme" files for some skins = auto()like theme.mp3 (or bg video)
    TEXT = auto()  # various text infos = auto()like BDinfo.txt or others...
    DOUBLE_EXT = (
        auto()
    )  # the filename startsWith video filename (and added extension) = auto()so we keep them...
    UNKNOWN = auto()

    @classmethod
    def from_media_artwork_type(
        cls: type[MediaFileType], a_type: MediaArtworkType
    ) -> MediaFileType:
        members = cls.__members__
        if a_type is MediaArtworkType.BACKGROUND:
            return MediaFileType.FANART
        elif a_type.name in members:
            return members[a_type.name]
        else:
            return cls.GRAPHIC

    @staticmethod
    def graph_type() -> list["MediaFileType"]:
        return [
            MediaFileType.BANNER,
            MediaFileType.CHARACTERART,
            MediaFileType.CLEARART,
            MediaFileType.CLEARLOGO,
            MediaFileType.DISC,
            MediaFileType.EXTRAFANART,
            MediaFileType.FANART,
            MediaFileType.EXTRATHUMB,
            MediaFileType.KEYART,
            MediaFileType.LOGO,
            MediaFileType.POSTER,
            MediaFileType.THUMB,
        ]

    def is_graph(self) -> bool:
        return self in MediaFileType.graph_type()


MediaFile: TypeAlias = tuple[MediaFileType, Path]


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

    def __init__(self, text: str, order: int) -> None:
        self.text = text
        self.order = order

    XLARGE = ("xlarge" + ": ~2000x3000px", 16)
    LARGE = ("large" + ": ~1000x1500px", 8)
    BIG = ("big" + ": ~500x750px", 4)
    MEDIUM = ("medium" + ": ~342x513px", 2)
    SMALL = ("small" + ": ~185x277px", 1)


class FanartSizes(Enum):
    """
    All available fanart sizes
    """

    def __init__(self, text: str, order: int) -> None:
        self.text = text
        self.order = order

    XLARGE = ("xlarge" + ": ~3840x2160px", 16)
    LARGE = ("large" + ": ~1920x1080px", 8)
    MEDIUM = ("medium" + ": ~1280x720px", 2)
    SMALL = ("small" + ": ~300x168px", 1)


@dataclass
class ImageSizeAndUrl:
    width: int
    height: int
    url: str


@dataclass
class MediaArtwork:
    provider_id: str = ""
    artwork_type: MediaArtworkType | None = None
    imdbId: str = ""
    tmdbId: int = 0
    season: int = -1
    preview_url: str = ""
    default_url: str = ""
    original_url: str = ""
    language: str = ""
    size_order: int = 0
    likes: int = 0
    animated: bool = False
    image_sizes: list[ImageSizeAndUrl] = field(default_factory=list)


@dataclass(kw_only=True)
class MediaEntity:
    dbid: UUID = field(default_factory=uuid4)
    locked: bool = False  # ignore
    data_source: str = ""  # TODO 暂时没有 data_source 的概念，可以存放首次发现的目录？
    ids: dict[str, str] = field(default_factory=dict)  # TODO 通过 key 来选择 scrapper
    title: str = ""
    original_title: str = ""
    year: int = 0
    plot: str = ""
    path: str = ""
    date_added: date = field(default_factory=date.today)
    production_company: str = ""
    scraped: bool = False
    note: str = ""
    ratings: dict[str, MediaRating] = field(default_factory=dict)
    media_files: list[MediaFile] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    artwork_url_map: dict[MediaFileType, str] = field(default_factory=dict)
    original_filename: str = ""
    last_scraper_id: str = ""
    last_scrape_language: str = ""
    newly_added: bool = False
    duplicate: bool = False
    # custom
    screen_size: str = ""
    audio_codec: str = ""

    def main_video(self) -> Path:
        return next(p for t, p in self.media_files if t is MediaFileType.VIDEO)

    def has_media_file(self, type_: MediaFileType) -> bool:
        return any(t for t, p in self.media_files if t is type_)

    def to_json(self):
        return json.dumps(self, cls=EntityJsonEncoder, indent=2)


@dataclass
class MediaTrailer:
    name: str = ""
    url: str = ""
    quality: str = ""
    provider: str = ""
    in_nfo: bool = False
    date: str = ""


class PersonType(Enum):
    ACTOR = auto()
    DIRECTOR = auto()
    WRITER = auto()
    PRODUCER = auto()
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
class MovieSet:
    name: str = ""
    overview: str = ""
    tmdb_id: int = 0


@dataclass(kw_only=True)
class Movie(MediaEntity):
    sort_title: str = ""
    tagline: str = ""
    runtime: int = 0
    watched: bool = False
    playcount: int = 0
    is_disc: bool = False
    spoken_languages: str = ""
    country: str = ""
    release_date: str = ""
    multi_movie_dir: bool = False  # 目录内是否有多个视频文件
    top250: int = 0
    media_source: str = ""  # TODO see guessit.rules.properties.source
    video_in_3d: bool = False
    certification: MediaCertification = MediaCertification.UNKNOWN
    edition: str = ""  # TODO see guessit.rules.properties.edition
    stacked: bool = False
    offline: bool = False
    genres: list[MediaGenres] = field(default_factory=list)
    extra_thumbs: list[str] = field(default_factory=list)
    extra_fanarts: list[str] = field(default_factory=list)
    actors: list[Person] = field(default_factory=list)
    producers: list[Person] = field(default_factory=list)
    directors: list[Person] = field(default_factory=list)
    writers: list[Person] = field(default_factory=list)
    trailer: list[MediaTrailer] = field(default_factory=list)
    showlinks: list[str] = field(default_factory=list)
    movie_set: MovieSet | None = None
    title_sortable: str = ""
    original_title_sortable = ""
    other_ids = ""
    localized_spoken_languages: str = ""


class MediaAiredStatus(Enum):
    def __init__(self, name_: str, possible_notations: list[str]) -> None:
        self.name_ = name_
        self.possible_notations = possible_notations

    UNKNOWN: tuple[str, list[str]] = ("Unknown", [])
    CONTINUING = ("Continuing", ["continuing", "returning series"])
    ENDED = ("Ended", ["ended"])

    @classmethod
    def retrieve_status(cls, val: str) -> "MediaAiredStatus":
        members = cls.__members__
        for m in members.values():
            if val.lower() in m.possible_notations:
                return m
        return MediaAiredStatus.UNKNOWN


@dataclass(kw_only=True)
class TvShow(MediaEntity):
    first_aired: str = ""  # date
    status: MediaAiredStatus = MediaAiredStatus.UNKNOWN
    runtime: int = 0  # 时长
    sort_title: str = ""
    certification: MediaCertification = MediaCertification.UNKNOWN
    country: str = ""
    genres: list[MediaGenres] = field(default_factory=list)
    actors: list[Person] = field(default_factory=list)
    dummy_episodes: list[TvShowEpisode] = field(default_factory=list)
    extra_fanart_urls: list[str] = field(default_factory=list)
    trailer: list[MediaTrailer] = field(default_factory=list)
    # 不用 dict 方便修改 season
    episodes: list[TvShowEpisode] = field(default_factory=list)
    # FIXME: 表示 TvShow 自身的元数据，不是本地文件的数据
    # tmdb 填充后才有数据，修改 episodes 不会动态更新该值
    seasons: list[TvShowSeason] = field(default_factory=list)

    def retrieve_episode(self, season: int, episode: int) -> "TvShowEpisode" | None:
        for e in self.episodes:
            if e.season == season and e.episode == episode:
                return e
        return None

    def episode_groupby_season(self) -> Iterator[tuple[int, Iterator["TvShowEpisode"]]]:
        e_sorted = sorted(self.episodes, key  = lambda x: (x.season, x.episode))
        return groupby(e_sorted, attrgetter("season"))




@dataclass(kw_only=True)
class TvShowSeason:
    season: int = -1
    air_date: str = ""  # date
    episode_count: int = 0
    name: str = ""
    plot: str = ""
    artwork_url_map: dict[MediaFileType, str] = field(default_factory=dict)


@dataclass(kw_only=True)
class TvShowEpisode(MediaEntity):
    episode: int = -1
    season: int = -1
    dvd_season: int = -1
    dvd_episode: int = -1
    display_season: int = -1
    display_episode: int = -1
    first_aired: str = ""  # date
    is_disc: bool = False
    multi_episode: bool = False
    is_dvd_order: bool = False
    stacked: bool = False  # TODO
    actors: list[Person] = field(default_factory=list)
    directors: list[Person] = field(default_factory=list)
    writers: list[Person] = field(default_factory=list)
    dummy: bool = False
    watched: bool = False
