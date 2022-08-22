from argparse import ArgumentParser
from pathlib import Path
from typing import Iterator


from peets.entities.movie import Movie
from itertools import chain, filterfalse


from peets.finder import traverse
from peets.scraper import search, fill




def main():
    parser = ArgumentParser(description="scrape movie")
    parser.add_argument('targets', type=Path, nargs='+')
    args = parser.parse_args()
    media_files = traverse(*args.targets)
    movie_set:Iterator[Movie] = (_create_movie(f)
              for f in chain(*map(_file_traverse, args.targets))
              if _movie_filter(f))

    for m in movie_set:
        breakpoint()
        results = search(m)
        fill(m, results[0]["id"])


if __name__ == "__main__":  # pragma: no cover
    main()
