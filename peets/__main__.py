from argparse import ArgumentParser
from pathlib import Path
from typing import Iterator


from peets.entities import MediaEntity, Movie
from peets.finder import traverse
from peets.guessit import NonMedia, create_entity
from peets.ui import interact, Action
from itertools import chain, filterfalse
from os import getcwd

def main():
    parser = ArgumentParser(description="scrape movie")
    parser.add_argument("-l", "--library",
                        type=Path,
                        default=getcwd(),
                        help="specify the library location, default is `cwd`")
    parser.add_argument('--naming', choices=["simple, full"], default="simple")
    parser.add_argument('targets', type=Path, nargs='+')
    args = parser.parse_args()
    media_files = traverse(*args.targets)
    media_set:Iterator[MediaEntity] = (e for e in (create_entity(f)
                                            for f in chain(*map(traverse, args.targets))
                                             )
                                 if not isinstance(e, NonMedia))

    for m in media_set:
        if interact(m, args.library, args.naming) is Action.QUIT:
            return


if __name__ == "__main__":  # pragma: no cover
    main()
