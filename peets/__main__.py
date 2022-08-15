from argparse import ArgumentParser
from pathlib import Path
from typing import Iterator

from guessit.rules.properties.title import title
from peets.entities.movie import Movie
from itertools import chain, filterfalse

from guessit import guessit

from peets.scraper import search, fill

MOVIE_CONTAINERS = [
        "3g2",
        "3gp",
        "3gp2",
        "asf",
        "avi",
        "divx",
        "flv",
        "iso",
        "m4v",
        "mk2",
        "mk3d",
        "mka",
        "mkv",
        "mov",
        "mp4",
        "mp4a",
        "mpeg",
        "mpg",
        "ogg",
        "ogm",
        "ogv",
        "qt",
        "ra",
        "ram",
        "rm",
        "ts",
        "vob",
        "wav",
        "webm",
        "wma",
        "wmv"
        ]

SUBTITLE_CONTAINERS = [
        "srt",
        "idx",
        "sub",
        "ssa",
        "ass"
      ]

def _movie_filter(target:Path):
    return target.suffix[1:] in MOVIE_CONTAINERS

def _file_traverse(target:Path)->Iterator[Path]:
    if target.is_dir():
        yield from filter(Path.is_file, target.glob("**/*"))
    else:
        yield target

# FIXME multiple file movie
def _create_movie(movie_file:Path)->Movie:
    """
    one file one movie
    """
    guess = guessit(movie_file)
    print(guess)
    return Movie(
        title = guess["title"],
        year = guess["year"],
        original_filename=movie_file.name,
        media_files=[str(movie_file)]
    )

def main():
    parser = ArgumentParser(description="scrape movie")
    parser.add_argument('targets', type=Path, nargs='+')
    args = parser.parse_args()
    movie_set:Iterator[Movie] = (_create_movie(f)
              for f in chain(*map(_file_traverse, args.targets))
              if _movie_filter(f))

    for m in movie_set:
        breakpoint()
        results = search(m)
        fill(m, results[0]["id"])


if __name__ == "__main__":  # pragma: no cover
    main()
