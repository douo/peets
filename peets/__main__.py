from argparse import ArgumentParser
from pathlib import Path
from typing import Iterator


from peets.entities import Movie
from peets.finder import traverse
from peets.guessit import create_entity
from peets.ui import interact, Action
from itertools import chain, filterfalse
from os import getcwd

def main():
    parser = ArgumentParser(description="scrape movie")
    parser.add_argument("-l", "--library",
                        type=Path,
                        default=getcwd(),
                        help="specify the library location, default is `cwd`")
    parser.add_argument('targets', type=Path, nargs='+')
    args = parser.parse_args()
    media_files = traverse(*args.targets)
    movie_set:Iterator[Movie] = (e for e in (create_entity(f)
                                            for f in chain(*map(traverse, args.targets))
                                             )
                                 if isinstance(e, Movie))

    for m in movie_set:
        if interact(m, args.library) is Action.QUIT:
            return


if __name__ == "__main__":  # pragma: no cover
    main()
