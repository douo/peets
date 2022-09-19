from enum import Enum, unique


@unique
class Language(Enum):
    """
    ISO-639-1
    copy from https://github.com/jonathan-shemer/iso639-1/blob/master/iso639_1/language.py
    """

    AB = "Abkhazian"
    AA = "Afar"
    AF = "Afrikaans"
    AK = "Akan"
    SQ = "Albanian"
    AM = "Amharic"
    AR = "Arabic"
    AN = "Aragonese"
    HY = "Armenian"
    AS = "Assamese"
    AV = "Avaric"
    AE = "Avestan"
    AY = "Aymara"
    AZ = "Azerbaijani"
    BM = "Bambara"
    BA = "Bashkir"
    EU = "Basque"
    BE = "Belarusian"
    BN = "Bengali"
    BH = "Bihari languages"
    BI = "Bislama"
    BS = "Bosnian"
    BR = "Breton"
    BG = "Bulgarian"
    MY = "Burmese"
    CA = "Catalan, Valencian"
    CH = "Chamorro"
    CE = "Chechen"
    NY = "Chichewa, Chewa, Nyanja"
    ZH = "Chinese"
    CV = "Chuvash"
    KW = "Cornish"
    CO = "Corsican"
    CR = "Cree"
    HR = "Croatian"
    CS = "Czech"
    DA = "Danish"
    DV = "Divehi, Dhivehi, Maldivian"
    NL = "Dutch, Flemish"
    DZ = "Dzongkha"
    EN = "English"
    EO = "Esperanto"
    ET = "Estonian"
    EE = "Ewe"
    FO = "Faroese"
    FJ = "Fijian"
    FI = "Finnish"
    FR = "French"
    FF = "Fulah"
    GL = "Galician"
    KA = "Georgian"
    DE = "German"
    EL = "Greek, Modern (1453-)"
    GN = "Guarani"
    GU = "Gujarati"
    HT = "Haitian, Haitian Creole"
    HA = "Hausa"
    HE = "Hebrew"
    HZ = "Herero"
    HI = "Hindi"
    HO = "Hiri Motu"
    HU = "Hungarian"
    IA = "Interlingua (International Auxiliary Language Association)"
    ID = "Indonesian"
    IE = "Interlingue, Occidental"
    GA = "Irish"
    IG = "Igbo"
    IK = "Inupiaq"
    IO = "Ido"
    IS = "Icelandic"
    IT = "Italian"
    IU = "Inuktitut"
    JA = "Japanese"
    JV = "Javanese"
    KL = "Kalaallisut, Greenlandic"
    KN = "Kannada"
    KR = "Kanuri"
    KS = "Kashmiri"
    KK = "Kazakh"
    KM = "Central Khmer"
    KI = "Kikuyu, Gikuyu"
    RW = "Kinyarwanda"
    KY = "Kirghiz, Kyrgyz"
    KV = "Komi"
    KG = "Kongo"
    KO = "Korean"
    KU = "Kurdish"
    KJ = "Kuanyama, Kwanyama"
    LA = "Latin"
    LB = "Luxembourgish, Letzeburgesch"
    LG = "Ganda"
    LI = "Limburgan, Limburger, Limburgish"
    LN = "Lingala"
    LO = "Lao"
    LT = "Lithuanian"
    LU = "Luba-Katanga"
    LV = "Latvian"
    GV = "Manx"
    MK = "Macedonian"
    MG = "Malagasy"
    MS = "Malay"
    ML = "Malayalam"
    MT = "Maltese"
    MI = "Maori"
    MR = "Marathi"
    MH = "Marshallese"
    MN = "Mongolian"
    NA = "Nauru"
    NV = "Navajo, Navaho"
    ND = "North Ndebele"
    NE = "Nepali"
    NG = "Ndonga"
    NB = "Norwegian Bokm√•l"
    NN = "Norwegian Nynorsk"
    NO = "Norwegian"
    II = "Sichuan Yi, Nuosu"
    NR = "South Ndebele"
    OC = "Occitan"
    OJ = "Ojibwa"
    CU = "Church¬†Slavic, Old Slavonic, Church Slavonic, Old Bulgarian, Old¬†Church¬†Slavonic"
    OM = "Oromo"
    OR = "Oriya"
    OS = "Ossetian, Ossetic"
    PA = "Panjabi, Punjabi"
    PI = "Pali"
    FA = "Persian"
    PL = "Polish"
    PS = "Pashto, Pushto"
    PT = "Portuguese"
    QU = "Quechua"
    RM = "Romansh"
    RN = "Rundi"
    RO = "Romanian, Moldavian, Moldovan"
    RU = "Russian"
    SA = "Sanskrit"
    SC = "Sardinian"
    SD = "Sindhi"
    SE = "Northern Sami"
    SM = "Samoan"
    SG = "Sango"
    SR = "Serbian"
    GD = "Gaelic, Scottish Gaelic"
    SN = "Shona"
    SI = "Sinhala, Sinhalese"
    SK = "Slovak"
    SL = "Slovenian"
    SO = "Somali"
    ST = "Southern Sotho"
    ES = "Spanish, Castilian"
    SU = "Sundanese"
    SW = "Swahili"
    SS = "Swati"
    SV = "Swedish"
    TA = "Tamil"
    TE = "Telugu"
    TG = "Tajik"
    TH = "Thai"
    TI = "Tigrinya"
    BO = "Tibetan"
    TK = "Turkmen"
    TL = "Tagalog"
    TN = "Tswana"
    TO = "Tonga (Tonga Islands)"
    TR = "Turkish"
    TS = "Tsonga"
    TT = "Tatar"
    TW = "Twi"
    TY = "Tahitian"
    UG = "Uighur, Uyghur"
    UK = "Ukrainian"
    UR = "Urdu"
    UZ = "Uzbek"
    VE = "Venda"
    VI = "Vietnamese"
    VO = "Volap√ºk"
    WA = "Walloon"
    CY = "Welsh"
    WO = "Wolof"
    FY = "Western Frisian"
    XH = "Xhosa"
    YI = "Yiddish"
    YO = "Yoruba"
    ZA = "Zhuang, Chuang"
    ZU = "Zulu"


@unique
class Country(Enum):
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
