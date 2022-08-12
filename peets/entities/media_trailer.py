from dataclasses import dataclass, field

@dataclass
class MediaTrailer:
    name:str = ""
    url:str = ""
    quality:str = ""
    provider:str = ""
    in_nfo:bool = False
    date:str = ""
