from argparse import ArgumentParser
from itertools import chain, filterfalse
from os import getcwd
from pathlib import Path
from typing import Iterator

from peets.entities import MediaEntity, Movie
from peets.finder import traverse
from peets.guessit import NonMedia, create_entity
from peets.library import Library
from peets.ui import Action
from peets.ui.entry import interact


def main():
    parser = ArgumentParser(description="scrape movie")
    parser.add_argument(
        "-l",
        "--library",
        type=Path,
        default=getcwd(),
        help="specify the library location, default is `cwd`",
    )
    parser.add_argument("--naming", choices=["simple, full"], default="simple")
    parser.add_argument("targets", type=Path, nargs="+")
    args = parser.parse_args()

    lib = Library(args.library)
    processed = set((r.source for r in lib.record_list))
    media_set: Iterator[tuple[Path, MediaEntity | NonMedia]] = (
        (f, create_entity(f, processed=processed))
        for f in chain(*map(traverse, args.targets))
    )

    for m in media_set:
        if isinstance(m[1], NonMedia):
            if any(m[0] == r.source for r in lib.record_list):
                print(f"Ingore: {m[0]} processed.")
        else:
            if interact(m[1], lib) is Action.QUIT:
                return


if __name__ == "__main__":  # pragma: no cover
    main()
