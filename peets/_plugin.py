import sys
from functools import cache
from typing import Any, Callable, TypeVar, cast

from pluggy import HookimplMarker, HookspecMarker, PluginManager

from peets.config import NAME, Config
from peets.nfo import Connector
from peets.nfo.kodi import CommonKodiConnector
from peets.scraper import Feature, MetadataProvider, Provider
from peets.tmdb import TmdbArtworkProvider, TmdbMetadataProvider

# 保留函数的 type annotations
_F = TypeVar("_F", bound=Callable[..., Any])
_spec_marker = HookspecMarker(NAME)
impl = HookimplMarker(NAME)
T = TypeVar("T")


def _spec(func: _F) -> _F:
    return cast(_F, _spec_marker(func))


@_spec
def get_providers(  # type: ignore[return,empty-body]
    config: Config,
) -> Provider | tuple[Provider, ...]:
    pass


@_spec
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
    return CommonKodiConnector(config)


def _flat(result: T | list[T | tuple[T]]) -> list[T]:
    if isinstance(result, list):
        data = []
        for i in result:
            if isinstance(result, tuple):
                data += cast(list[T], i)
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

    @cache
    def get_connectors(self) -> list[Connector]:
        return _flat(self.manager.hook.get_connectors(config=self.config))

    def connectors(self, media: T) -> list[Connector[T]]:
        return [c for c in self.get_connectors() if c.is_available(media)]

    def metadata(self, media: T) -> list[MetadataProvider[T]]:
        return [
            p
            for p in self.get_providers()
            if p.is_available(media) and isinstance(p, MetadataProvider)
        ]

    def artwork(self, media: T) -> list[Provider[T]]:
        return [
            p
            for p in self.get_providers()
            if p.is_available(media) and Feature.Artwork in p.features
        ]
