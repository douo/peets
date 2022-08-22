from datetime import datetime
from tmdbsimple.movies import Movies
from peets.entities.media_artwork import MediaArtwork, MediaArtworkType
from peets.entities.movie import Movie
from peets.entities.media_entity import MediaRating
from peets.merger import replace
import tmdbsimple as tmdb

tmdb.API_KEY = "42dd58312a5ca6dd8339b6674e484320"


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

# _enable_log()

def search(movie: Movie):
    api = tmdb.Search()
    resp = api.movie(
        query = movie.title,
        include_adult = True,
        year = movie.year,
    )
    results = api.results
    for s in results:
         print(s['title'], s['id'], s['release_date'], s['popularity'])
    return results

def fill(movie: Movie, _id: int) -> Movie:
    p_id = "tmdb"
    artwork_base_url = "https://image.tmdb.org/t/p/"
    language = "zh-CN"
    api = tmdb.Movies(_id)
    context = api.info(
        language=language,
        append_to_response="credits,keywords,release_dates,translations"
    )
    # breakpoint()

    table = [
        ("overview", "plot"),
        (("vote_average", "vote_count"),
         "ratings",
         lambda va, vc : ("tmdb", MediaRating(rating_id = "tmdb", rating=va, votes=vc))
         ),
        (("poster_path", "id"), "artwork_url_map",  #TODO download
         lambda path, id: (MediaArtworkType.POSTER, f"{artwork_base_url}w342{path}")
         # MediaArtwork(
         #     provider_id="tmdb",
         #     artwork_type=MediaArtworkType.POSTER,
         #     preview_url=f"{artwork_base_url}w342{path}",
         #     default_url=f"{artwork_base_url}original{path}",
         #     original_url=f"{artwork_base_url}original{path}",
         #     language=language,
         #     tmdbId=id
         ), # 列表类型，返回单项表示插入？？
        ("spoken_languages","spoken_languages",
         lambda spoken_languages: ", ".join([lang["iso_639_1"] for lang in spoken_languages])),
        ("production_countries", "country",
         lambda production_countries: ", ".join([country["iso_3166_1"] for country in production_countries])),
        ("imdb_id","ids", lambda _id: ("imdb", _id)), # dict 类型的返回 (key value)
        ("id","ids", lambda _id: ("tmdb", _id)),
        ("production_companies", "production_company",
         lambda production_companies: ", ".join([company["name"] for company in production_companies])),
        #TODO release_dates TmdbMovieMetadataProvider#L834
        # 一对多的情况下，支持通过 tuple 指定
        # 转换函数表示默认赋值
        ("release_date", ("release_date", "year"), (None, lambda release_date: datetime.strptime(release_date, "%Y-%m-%d").year)),
        #TODO credits
        #TODO genres 能自动创建枚举外的类型
        #TODO belongs_to_collections
        ("keywords", "tags", None)
    ]

    return replace(movie, context, table)
