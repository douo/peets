from pathlib import Path
from guessit import guessit
from peets.entities import Movie, MediaEntity
from peets.error import UnknownMediaTypeError
from peets.merger import create
from peets.finder import  is_subtitle, is_subtitle, is_video




# FIXME multiple file movie
def create_entity(path: Path)->MediaEntity:
    """
    one file one movie
    """
    guess = guessit(path)

    match guess["type"]:
        case "movie":
            return _create_movie(guess, path)
        case _:
            raise UnknownMediaTypeError(guess)

def _create_movie(guess: dict, path: Path)->Movie: # type: ignore
    # check multiple movie in dir
    multi_movie_dir = False
    subtitles = list()
    for child in path.parent.iterdir():
        if child is not path:
            if is_video(child):
                multi_movie_dir = True # TODO 排除掉 Trailer 或者广告之类的视频
            elif is_subtitle(child):
                subtitles.append(child)


    return create(Movie, guess)
