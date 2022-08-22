from pathlib import Path
from peets.entities.movie import Movie

from peets.guessit import create_entity
from guessit import guessit


def _create_file(name:str, parent:Path):
    f = parent.joinpath(name)
    parent.mkdir(parents=True, exist_ok=True)
    f.touch()
    return f


def test_create_entity(tmp_path):
    f = _create_file("Hight.Town.2020.AAC-HE_LC_8ch.mkv", tmp_path)

    movie = create_entity(f)

    assert isinstance(movie, Movie)
    assert movie.title == "Hight Town"
    assert movie.year == 2020
