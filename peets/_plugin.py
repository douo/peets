import sys
from functools import cache
from typing import Any, Callable, TypeVar, cast

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
from peets.ui.action import MediaUI, MovieUI, TvShowUI
from peets.entities import MediaEntity

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
def get_providers(  # type: ignore[return,empty-body]
    config: Config,
) -> Provider | tuple[Provider, ...]:
    pass


@spec
def get_connectors(  # type: ignore[return,empty-body]
    config: Config,
) -> Connector | tuple[Provider, ...]:
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
def provide_uis() -> type[U] | tuple[type[U], ...]:  # type: ignore[return,empty-body]
    pass


@impl(specname="provide_uis")
def provide_uis_impl() -> type[U] | tuple[type[U], ...]:
    return (MovieUI, TvShowUI)


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
    def __init__(self, config) -> None:
        self.manager: PluginManager = PluginManager(NAME)
        self.config = config
        self.manager.add_hookspecs(sys.modules[__name__])
        self._register_internal()

    def _register_internal(self) -> None:
        self.register(sys.modules[__name__])
        self.manager.load_setuptools_entrypoints(NAME)

    def register(self, module_or_class) -> None:
        self.manager.register(module_or_class)

    @cache
    def get_providers(self) -> list[Provider]:
        return _flat(self.manager.hook.get_providers(config=self.config))

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
        return _flat(self.manager.hook.get_connectors(config=self.config))

    def connectors(self, media: E) -> list[Connector[E]]:
        return [c for c in self.get_connectors() if c.is_available(media)]

    def get_ui(self, type_: type[E]) -> type[U]:
        uis = provide_uis_impl()
        target = f"{type_.__name__}UI"
        return next(u for u in uis if u.__name__ == target)
