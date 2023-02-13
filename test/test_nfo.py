from pylsp import hookspecs
from peets.config import Config
from peets._plugin import Plugin

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
from peets.tmdb import TmdbMetadataProvider
from peets.nfo import pprint
from peets.nfo.kodi import MovieKodiConnector, TvShowKodiConnector, TvShowEpisodeKodiConnector



def test_detail(hijack, dummy):
    # m = dummy(Movie)  # FIXME buggy
    print = pprint
    data = hijack("movie.json")
    tmdb = TmdbMetadataProvider(Config())
    m = tmdb.apply(Movie(), id_=0)
    c = MovieKodiConnector(Config())
    print(c.generate(m))


    hijack("tvshow.json", "tmdbsimple.TV._GET")
    hijack("season.json", "tmdbsimple.TV_Seasons._GET")
    episodes = [TvShowEpisode(season=1, episode=1)]
    m = tmdb.apply(TvShow(episodes=episodes), id_=0)

    c = TvShowKodiConnector(Config())
    print(c.generate(m))

    for e in m.episodes:
        c = TvShowEpisodeKodiConnector(Config())
        print(c.generate(e, belong_to=m))
