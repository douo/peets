from peets.scraper import register
from peets.nfo import register as nfo_register
from peets.nfo.kodi.movie import MovieKodiConnector
from peets.tmdb import TmdbArtworkProvider, TmdbMovieMetadata
from peets.iso import Language, Country

lang = Language.ZH
country = Country.CN

register(TmdbArtworkProvider(lang, country),
         TmdbMovieMetadata(lang, country))

nfo_register(MovieKodiConnector("kodi"))
