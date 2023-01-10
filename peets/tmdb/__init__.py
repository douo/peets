import tmdbsimple as tmdb
from .artwork import TmdbArtworkProvider
from .metadata import TmdbMetadataProvider


__all__ = (
    "TmdbArtworkProvider",
    "TmdbMetadataProvider"
)

tmdb.API_KEY = "42dd58312a5ca6dd8339b6674e484320"
