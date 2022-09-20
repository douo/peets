from peets.tmdb import TmdbMovieMetadata, TmdbArtworkProvider
from peets.nfo import generate_nfo
from peets.entities import MediaFileType, Movie, MediaCertification, MovieSet
from peets.iso import Language, Country
import os
import json
from distutils import dir_util
from pytest import fixture

def test_detail(datadir, mocker):
    with open(f"{datadir}/movie.json") as f:
        data = json.load(f)

    mocker.patch(
        "tmdbsimple.Movies._GET",
        return_value=data
    )

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

def test_artwork(datadir, mocker):
    with open(f"{datadir}/movie_images.json") as f:
        data = json.load(f)

    mocker.patch(
        "tmdbsimple.Movies._GET",
        return_value=data
    )
    tmdb = TmdbArtworkProvider(language=Language.ZH,
                             country=Country.CN)

    m = tmdb.apply(Movie(ids={"tmdb": 0}))

    assert m.artwork_url_map == {
        MediaFileType.POSTER: "https://image.tmdb.org/t/p/original/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
        MediaFileType.FANART: "https://image.tmdb.org/t/p/original/5pxdgKVEDWDQBtvqIB2eB2oheml.jpg"
    }

def test_metadata_original_release_date_only(datadir, mocker):
    with open(f"{datadir}/movie_original_release_date_only.json") as f:
        data = json.load(f)

    mocker.patch(
        "tmdbsimple.Movies._GET",
        return_value=data
    )

    tmdb = TmdbMovieMetadata(language=Language.ZH,
                             country=Country.CN)
    m = tmdb.apply(Movie(), id_=0)

    assert m.release_date == "2022-07-08"

def test_metadata_certification(datadir, mocker):
    with open(f"{datadir}/movie_certification.json") as f:
        data = json.load(f)

    mocker.patch(
        "tmdbsimple.Movies._GET",
        return_value=data
    )

    tmdb = TmdbMovieMetadata(language=Language.ZH,
                             country=Country.CN)
    m = tmdb.apply(Movie(), id_=0)

    assert m.certification == MediaCertification.US_PG13


@fixture
def datadir(tmpdir, request):
    '''
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.
    '''
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    if os.path.isdir(test_dir):
        dir_util.copy_tree(test_dir, str(tmpdir))

    return tmpdir
