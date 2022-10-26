from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeAlias, TypeVar
from peets.entities import MediaEntity, MediaFileType
from peets.merger import replace
from enum import Enum, auto


T = TypeVar('T', bound=MediaEntity)

@dataclass
class SearchResult:
    id_: Any
    title: str
    source: str
    year: int = 0
    rank: float = 0

class Feature(Enum):
    Metadata = auto()
    Artwork = auto()

class Provider(ABC, Generic[T]):
    @abstractmethod
    def apply(self, media: T, **kwargs) -> T:
        pass

    @property
    @abstractmethod
    def available_type(self) -> list[str]:
        pass

    @property
    @abstractmethod
    def features(self) -> list[Feature]:
        pass

    def is_available(self, media: T) -> bool:
        return type(media).__name__.lower() in [t.lower() for t in self.available_type()]

class MetadataProvider(Provider[T], Generic[T]):
    @abstractmethod
    def search(self, media: T) -> list[SearchResult]:
        pass

    @property
    def features(self) -> list[Feature]:
        return [Feature.Metadata]

global providers
providers: list[Provider] = []

def register(*p: Provider):
    global providers
    providers += p

def metadata(media: T) -> list[MetadataProvider[T]]:
    global providers
    return [p for p in providers
        if p.is_available(media) and isinstance(p, MetadataProvider)
    ]

def artwork(media: T) -> list[Provider[T]]:
    global providers
    return [
        p for p in providers
        if p.is_available(media) and Feature.Artwork in p.features()
    ]
