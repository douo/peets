from peets.tmdb import TmdbMovieMetadata, TmdbArtworkProvider
from peets.nfo import generate_nfo
from peets.entities import MediaFileType, Movie, MediaCertification, MovieSet
from peets.iso import Language, Country
import os
import json
from pytest import fixture
from util import datadir

def test_detail(hijack, mocker):
    data = hijack("movie.json")

    tmdb = TmdbMovieMetadata(language=Language.ZH,
                             country=Country.CN)
    m = tmdb.apply(Movie(), id_=0)

    assert m.ids["imdb"] ==  data["imdb_id"]
    assert int(m.ids["tmdb"]) == data["id"]
    assert m.release_date == "2022-07-08"
    assert m.certification == MediaCertification.US_PG13
    assert m.movie_set.tmdb_id == 131296
    assert m.ids["tmdbSet"] == '131296'
    # print(generate_nfo(m))

def test_artwork(hijack, mocker):
    data = hijack("movie_images.json")

    tmdb = TmdbArtworkProvider(language=Language.ZH,
                             country=Country.CN)

    m = tmdb.apply(Movie(ids={"tmdb": 0}))

    assert m.artwork_url_map == {
        MediaFileType.POSTER: "https://image.tmdb.org/t/p/original/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
        MediaFileType.FANART: "https://image.tmdb.org/t/p/original/5pxdgKVEDWDQBtvqIB2eB2oheml.jpg"
    }

def test_metadata_original_release_date_only(hijack, mocker):
    hijack("movie_original_release_date_only.json")

    tmdb = TmdbMovieMetadata(language=Language.ZH,
                             country=Country.CN)
    m = tmdb.apply(Movie(), id_=0)

    assert m.release_date == "2022-07-08"

def test_metadata_certification(hijack, mocker):
    hijack("movie_certification.json")
    tmdb = TmdbMovieMetadata(language=Language.ZH,
                             country=Country.CN)
    m = tmdb.apply(Movie(), id_=0)

    assert m.certification == MediaCertification.US_PG13


@fixture
def hijack(datadir, mocker, request):
    def _inner(name:str):
        with open(f"{datadir}/{name}") as f:
            data = json.load(f)

        mocker.patch(
                "tmdbsimple.Movies._GET",
            return_value=data
        )
        return data
    return _inner
