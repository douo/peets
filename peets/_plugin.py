from __future__ import annotations

import sys
from functools import cache
from typing import TYPE_CHECKING, Any, Callable, TypeVar, cast

from pluggy import HookimplMarker, HookspecMarker, PluginManager

from peets.config import NAME, Config
from peets.nfo import Connector
from peets.nfo.kodi import (
    MovieKodiConnector,
    TvShowEpisodeKodiConnector,
    TvShowKodiConnector,
)
from peets.scraper import Feature, MetadataProvider, Provider
from peets.tmdb import TmdbArtworkProvider, TmdbMetadataProvider
from peets.ui import MediaUI, MovieUI, TvShowUI
from peets.entities import MediaEntity


if TYPE_CHECKING:
    from peets.library import Library


# 保留函数的 type annotations
_F = TypeVar("_F", bound=Callable[..., Any])
_spec_marker = HookspecMarker(NAME)
impl = HookimplMarker(NAME)
T = TypeVar("T")
E = TypeVar("E", bound=MediaEntity)
U = MediaUI[Any]


def spec(func: _F) -> _F:
    return cast(_F, _spec_marker(func))


@spec
def get_providers(
    config: Config,
) -> Provider | tuple[Provider, ...]:  # type: ignore[return,empty-body]
    pass


@spec
def get_connectors(
    config: Config,
) -> Connector | tuple[Provider, ...]:  # type: ignore[return,empty-body]
    pass


@impl(specname="get_providers")
def get_providers_impl(config: Config) -> Provider | tuple[Provider, ...]:
    return (
        TmdbArtworkProvider(config),
        TmdbMetadataProvider(config),
    )


@impl(specname="get_connectors")
def get_connectors_impl(config: Config) -> Connector | tuple[Connector, ...]:
    return (
        TvShowKodiConnector(config),
        MovieKodiConnector(config),
        TvShowEpisodeKodiConnector(config),
    )


@spec
def provide_uis(lib: Library) -> U | tuple[U, ...]:  # type: ignore[return,empty-body]
    pass


@impl(specname="provide_uis")
def provide_uis_impl(lib: Library) -> U | tuple[U, ...]:
    return (MovieUI(lib), TvShowUI(lib))


def _flat(result: T | list[T | tuple[T]]) -> list[T]:
    if isinstance(result, list):
        data = []
        for i in result:
            if isinstance(i, tuple):
                data += list(cast(tuple[T], i))
            else:
                data.append(i)
        return data
    else:
        return [result]


class Plugin:
    def __init__(self, lib: Library) -> None:
        self.manager: PluginManager = PluginManager(NAME)
        self.lib = lib
        self.manager.add_hookspecs(sys.modules[__name__])
        self._register_internal()

    def _register_internal(self) -> None:
        self.register(sys.modules[__name__])
        self.manager.load_setuptools_entrypoints(NAME)

    def register(self, module_or_class) -> None:
        self.manager.register(module_or_class)

    @cache
    def get_providers(self) -> list[Provider]:
        return _flat(self.manager.hook.get_providers(config=self.lib.config))  # type: ignore

    def metadata(self, media: E) -> list[MetadataProvider[E]]:
        return [
            p
            for p in self.get_providers()
            if p.is_available(media) and isinstance(p, MetadataProvider)
        ]

    def artwork(self, media: E) -> list[Provider[E]]:
        return [
            p
            for p in self.get_providers()
            if p.is_available(media) and Feature.Artwork in p.features
        ]

    @cache
    def get_connectors(self) -> list[Connector]:
        return _flat(self.manager.hook.get_connectors(config=self.lib.config))  # type: ignore

    def connectors(self, media: E) -> list[Connector[E]]:
        return [c for c in self.get_connectors() if c.is_available(media)]

    @cache
    def _get_ui(self, type_ : type[E]) -> U:
        uis = _flat(self.manager.hook.provide_uis(lib=self.lib))  # type: ignore
        target = f"{type_.__name__}UI"
        return next(u for u in uis if type(u).__name__ == target)

    def get_ui(self, media: E) -> U:
        return self._get_ui(type(media))
