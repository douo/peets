from enum import Enum

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
