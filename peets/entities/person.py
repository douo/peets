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
    persion_type: Type = Type.OTHER
    name: str = ""
    role: str | None = None
    thumb_url: str | None = None
    profile_url: str | None = None
    ids: dict = field(default_factory=dict)
