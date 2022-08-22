from peets.scraper import fill
from peets.entities.movie import Movie
import os
import json
from distutils import dir_util
from pytest import fixture

def test_fill(datadir, mocker):
    with open(f"{datadir}/movie.json") as f:
        data = json.load(f)

    mocker.patch(
        "tmdbsimple.Movies._GET",
        return_value=data
    )

    _id = 6160
    m = fill(Movie(), _id)



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
