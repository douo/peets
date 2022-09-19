from peets.scraper import register
from peets.tmdb import TmdbArtworkProvider, TmdbMovieMetadata
from peets.iso import Language, Country

lang = Language.ZH
country = Country.CN

register(TmdbArtworkProvider(lang, country),
         TmdbMovieMetadata(lang, country))
