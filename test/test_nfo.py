from peets.nfo import connector

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
from peets.tmdb import TmdbMovieMetadata


def test_detail(hijack, dummy):
    # m = dummy(Movie)  # FIXME buggy
    data = hijack("movie.json")
    tmdb = TmdbMovieMetadata(language=Language.ZH, country=Country.CN)
    m = tmdb.apply(Movie(), id_=0)
    c = connector(m)[0]
    print(c.generate(m))
