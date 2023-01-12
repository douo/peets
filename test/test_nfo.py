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
from peets import manager, get_config
from peets.tmdb import TmdbMetadataProvider
from peets.nfo import pprint


def test_detail(hijack, dummy):
    # m = dummy(Movie)  # FIXME buggy
    print = pprint
    data = hijack("movie.json")
    tmdb = TmdbMetadataProvider(get_config())
    m = tmdb.apply(Movie(), id_=0)
    c = manager.connectors(m)[0]
    print(c.generate(m))


    hijack("tvshow.json", "tmdbsimple.TV._GET")
    hijack("season.json", "tmdbsimple.TV_Seasons._GET")
    episodes = [TvShowEpisode(season=1, episode=1)]
    m = tmdb.apply(TvShow(episodes=episodes), id_=0)

    c = manager.connectors(m)[0]
    print(c.generate(m))
