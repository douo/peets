from pylsp import hookspecs

from peets.entities import (
    MediaAiredStatus,
    MediaCertification,
    MediaFileType,
    MediaGenres,
    Movie,
    TvShow,
    TvShowEpisode,
)
from peets.iso import Country, Language
from peets import manager
from peets.tmdb import TmdbMetadataProvider


def test_detail(hijack, dummy):
    # m = dummy(Movie)  # FIXME buggy
    data = hijack("movie.json")
    tmdb = TmdbMetadataProvider(language=Language.ZH, country=Country.CN)
    m = tmdb.apply(Movie(), id_=0)
    c = manager.connectors(m)[0]
    print(c.generate(m))
