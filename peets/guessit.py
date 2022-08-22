from pathlib import Path
from guessit import guessit
from peets.entities.movie import Movie
from peets.entities.media_entity import MediaEntity
from peets.error import UnknownMediaTypeError
from peets.merger import create


# FIXME multiple file movie
def create_entity(path:Path)->MediaEntity:
    """
    one file one movie
    """
    guess = guessit(path)

    match guess["type"]:
        case "movie":
            return _create_movie(guess, path)
        case _:
            raise UnknownMediaTypeError(guess)



def _create_movie(guess:dict,path:Path)->Movie: # type: ignore
    return create(Movie, guess)
