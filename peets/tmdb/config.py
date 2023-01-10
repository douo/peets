import tmdbsimple as tmdb
from peets import get_config

PROVIDER_ID = "tmdb"
_ARTWORK_BASE_URL = "https://image.tmdb.org/t/p/"
_PROFILE_BASE_URL = "https://www.themoviedb.org/"

tmdb.API_KEY = get_config().tmdb_key

def _enable_log():
    import logging
    try: # for Python 3
        from http.client import HTTPConnection
    except ImportError:
        from httplib import HTTPConnection
    HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

#_enable_log()
