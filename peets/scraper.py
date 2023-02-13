from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Generic, TypeVar

from peets.entities import MediaEntity


T = TypeVar("T", bound=MediaEntity)


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

    @property
    @abstractmethod
    def source(self) -> str:
        pass


    def is_available(self, media: T) -> bool:
        return type(media).__name__.lower() in [
            t.lower() for t in self.available_type
        ]


class MetadataProvider(Provider[T], Generic[T]):
    @abstractmethod
    def search(self, media: T) -> list[SearchResult]:
        pass

    @property
    def features(self) -> list[Feature]:
        return [Feature.Metadata]
