from dataclasses import dataclass, field
from enum import Enum, auto

class Type(Enum):
    ACTOR = auto(),
    DIRECTOR = auto(),
    WRITER = auto(),
    PRODUCER = auto(),
    OTHER = auto()

@dataclass
class Person:
    persion_type:Type = Type.OTHER
    name:str = ""
    role:str = ""
    thumb_url:str = ""
    profile_url:str = ""
    ids:dict = field(default_factory=dict)
