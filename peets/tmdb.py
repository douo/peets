from datetime import datetime
from tmdbsimple.movies import Movies
from peets.entities import Movie, MediaFileType, MediaRating, MediaGenres, MediaArtwork, MediaArtworkType, Person, PersonType
from peets.merger import replace
import tmdbsimple as tmdb

tmdb.API_KEY = "42dd58312a5ca6dd8339b6674e484320"

PROVIDER_ID = "tmdb"
_ARTWORK_BASE_URL = "https://image.tmdb.org/t/p/"
_PROFILE_BASE_URL = "https://www.themoviedb.org/"

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
    return results

def _credits_filter(person_type: PersonType):
    if person_type is PersonType.ACTOR:
        credits_type = "cast"
        filter_ = lambda c: True
    elif person_type is PersonType.DIRECTOR:
        credits_type = "crew"
        filter_ = lambda c: "job" in c and c["job"] == "Director"
    elif person_type is PersonType.WRITER:
        credits_type = "crew"
        filter_ = lambda c: "department" in c and c["department"] == "Writing"
    elif person_type is PersonType.PRODUCER:
        credits_type = "crew"
        filter_ = lambda c: "department" in c and c["department"] == "Production"
    else:
        raise Exception(f"Unkonw PersonType {person_type}")

    def _conv(credit):
        return Person(
            persion_type= person_type,
            ids={PROVIDER_ID: credit["id"]},
            name= credit["name"],
            role= credit["character"] if "character" in credit else None,
            thumb_url=f"{_ARTWORK_BASE_URL}h632{credit['profile_path']}" if "profile_path" in credit else None,
            profile_url=f"{_PROFILE_BASE_URL}{credit['id']}" if "id" in credit else None
        )
    def _execute(credits):
        data = credits[credits_type]
        return [_conv(c) for c in data if filter_(c)]

    return _execute

def _to_genre(tmdb_genre):
    match int(tmdb_genre["id"]):
        case 28 | 10759:
            return MediaGenres.ACTION
        case 12:
            return MediaGenres.ADVENTURE
        case 16:
            return MediaGenres.ANIMATION
        case 35:
            return MediaGenres.COMEDY
        case 80:
            return MediaGenres.CRIME
        case 105:
            return MediaGenres.DISASTER
        case 99:
            return MediaGenres.DOCUMENTARY
        case 18:
            return MediaGenres.DRAMA
        case 82:
            return MediaGenres.EASTERN
        case 2916:
            return MediaGenres.EROTIC
        case 10751:
            return MediaGenres.FAMILY
        case 14:
            return MediaGenres.FANTASY
        case 10753:
            return MediaGenres.FILM_NOIR
        case 10769:
            return MediaGenres.FOREIGN
        case 36:
            return MediaGenres.HISTORY
        case 10595:
            return MediaGenres.HOLIDAY
        case 27:
            return MediaGenres.HORROR
        case 10756:
            return MediaGenres.INDIE
        case 10402:
            return MediaGenres.MUSIC
        case 22:
            return MediaGenres.MUSICAL
        case 9648:
            return MediaGenres.MYSTERY
        case 10754:
            return MediaGenres.NEO_NOIR
        case 10763:
            return MediaGenres.NEWS
        case 10764:
            return MediaGenres.REALITY_TV
        case 1115:
            return MediaGenres.ROAD_MOVIE
        case 10749:
            return MediaGenres.ROMANCE
        case 878 | 10765:
            return MediaGenres.SCIENCE_FICTION
        case 10755:
            return MediaGenres.SHORT
        case 10766:
            return MediaGenres.SOAP
        case 9805:
            return MediaGenres.SPORT
        case 10758:
            return MediaGenres.SPORTING_EVENT
        case 10757:
            return MediaGenres.SPORTS_FILM
        case 10748:
            return MediaGenres.SUSPENSE
        case 10767:
            return MediaGenres.TALK_SHOW
        case 10770:
            return MediaGenres.TV_MOVIE
        case 53:
            return MediaGenres.THRILLER
        case 10752 | 10768:
            return MediaGenres.WAR
        case 37:
            return MediaGenres.WESTERN
        case _: # 能自动创建枚举外的类型
            return tmdb_genre


def fill(movie: Movie, _id: int) -> Movie:

    language = "zh-CN"
    api = tmdb.Movies(_id)
    context = api.info(
        language=language,
        append_to_response="credits,keywords,release_dates,translations"
    )
    # breakpoint()

    table = [
        ("imdb_id","ids", lambda id_: ("imdb", str(id_))), # dict 类型的返回 (key value)
        ("id","ids", lambda id_: (PROVIDER_ID, str(id_))),
        ("overview", "plot"),
        (("vote_average", "vote_count"),
         "ratings",
         lambda va, vc : (PROVIDER_ID, MediaRating(rating_id = "tmdb", rating=va, votes=vc))
         ),
        (("poster_path", "id"), "artwork_url_map",  #TODO artwork 应该另外处理？
         lambda path, id_: (MediaFileType.POSTER, f"{_ARTWORK_BASE_URL}w342{path}")
         # MediaArtwork(
         #     provider_id=PROVIDER_ID,
         #     artwork_type=MediaArtworkType.POSTER,
         #     preview_url=f"{artwork_base_url}w342{path}",
         #     default_url=f"{artwork_base_url}original{path}",
         #     original_url=f"{artwork_base_url}original{path}",
         #     language=language,
         #     tmdbId=id_
         ), # 列表类型，返回单项表示插入？？
        ("spoken_languages","spoken_languages",
         lambda spoken_languages: ", ".join([lang["iso_639_1"] for lang in spoken_languages])),
        ("production_countries", "country",
         lambda production_countries: ", ".join([country["iso_3166_1"] for country in production_countries])),
        ("production_companies", "production_company",
         lambda production_companies: ", ".join([company["name"] for company in production_companies])),
        #TODO release_dates TmdbMovieMetadataProvider#L834
        # 一对多的情况下，支持通过 tuple 指定
        # 转换函数表示默认赋值
        ("release_date", ("release_date", "year"), (None, lambda release_date: datetime.strptime(release_date, "%Y-%m-%d").year)),
        #credits TODO partition
        ("credits", ("actors", "producers", "directors", "writers"),
         (_credits_filter(PersonType.ACTOR), _credits_filter(PersonType.PRODUCER), _credits_filter(PersonType.DIRECTOR), _credits_filter(PersonType.WRITER))),
        #genres
        ("genres", "genres", lambda genres: [_to_genre(g) for g in genres]),
        ("adult", "genres", lambda adult: MediaGenres.EROTIC if adult else []),
        #TODO belongs_to_collections
        ("keywords", "tags", lambda keywords: [k["name"] for k in keywords["keywords"]])
    ]

    return replace(movie, context, table)
