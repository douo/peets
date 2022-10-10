from peets.tmdb import TmdbMovieMetadata, TmdbArtworkProvider
from peets.nfo import generate_nfo
from peets.entities import MediaAiredStatus, MediaFileType, MediaGenres, Movie, MediaCertification, MovieSet, TvShow
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

def test_tvshow(hijack, mocker):
    hijack("tvshow.json")
    tmdb = TmdbMovieMetadata(language=Language.ZH,
                             country=Country.CN)
    m = tmdb.apply(TvShow(), id_=0)

    assert m.ids["tmdb"] == "95396"
    assert m.title == "Severance"
    assert m.first_aired == "2022-02-17"
    assert m.country == "US"
    assert m.runtime == 50
    assert m.production_company == "Apple TV+, Red Hour, Endeavor Content, Fifth Season"
    assert m.status == MediaAiredStatus.CONTINUING
    assert m.year == 2022
    assert len(m.actors) == 10
    assert m.ids["imdb"] == "tt11280740"
    assert m.ids["tvdb"] == "371980"
    assert m.certification == MediaCertification.US_TVMA
    assert set(m.genres) == {MediaGenres.DRAMA, MediaGenres.SCIENCE_FICTION, MediaGenres.MYSTERY}



@fixture
def hijack(datadir, mocker, request):
    def _inner(name:str):
        with open(f"{datadir}/{name}") as f:
            data = json.load(f)

        mocker.patch(
                "tmdbsimple.base.TMDB._GET",
            return_value=data
        )
        return data
    return _inner
