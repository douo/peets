from .artwork import TmdbArtworkProvider
from .metadata import TmdbMetadataProvider

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


__all__ = (
    "TmdbArtworkProvider",
    "TmdbMetadataProvider"
)
