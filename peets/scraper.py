from dataclasses import dataclass
from datetime import datetime
from tmdbsimple.movies import Movies
from peets.entities.media_artwork import MediaArtwork, MediaArtworkType
from peets.entities.movie import Movie
from peets.entities.media_entity import MediaRating
import tmdbsimple as tmdb
from typing import Any
from itertools import chain
tmdb.API_KEY = "42dd58312a5ca6dd8339b6674e484320"


def search(movie:Movie):
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

def fill(movie:Movie, _id:int):
    p_id = "tmdb"
    artwork_base_url = "https://image.tmdb.org/t/p/"
    language = "zh-CN"
    api = tmdb.Movies(_id)
    context = api.info(language=language)


    map_table = [
        ("overview", "plot", None),
        (("vote_average", "vote_count"),
         "ratings",
         lambda va, vc : MediaRating(rating_id = "tmdb", rating=va, votes=vc)
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

    _merge_json(movie, context, map_table)

def _make_sure_tuple(obj) -> tuple[Any]:
    return obj if isinstance(obj, tuple) else(obj,)

def _merge_json(base:Movie, addon:dict[str,Any], map_table:list[tuple]):
    # make sure all item is tuple
    _map_table = list(map(lambda i: tuple(map(lambda j:  _make_sure_tuple(j), i)), map_table))

    used = set(chain(*map(lambda i: i[0], _map_table)))

    base_fields = base.__dataclass_fields__

    _map_table += [((k,), (k,), (None,)) for k in addon.keys() if k not in used and k in base_fields]

    for item in _map_table:
        key, target, converter = item
        print(item)
        values = tuple(map(addon.get, key))
        for attr, conv in zip(target, converter):
            v = conv(*values) if conv is not None else values[0]
            _field = base_fields[attr]
            if _field.type is list:
                _v = getattr(base, attr)
                if _v is None:
                    setattr(base, attr, v if isinstance(v, list) else [v])
                elif isinstance(v, list):
                    setattr(base, attr, v)
                else:
                    _v.append(v)
            elif _field.type is dict:
                _v = getattr(base, attr)
                if isinstance(v, dict):
                    setattr(base, attr, v)
                elif isinstance(v, tuple) and len(v) == 2:
                    if _v is None:
                        _v = dict()
                        setattr(base, attr, _v)
                    _v[v[0]] = v[1]
            else:
                setattr(base, attr, v)
