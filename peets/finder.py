from pathlib import Path
from typing import Iterator
from itertools import chain
from peets.const import SUBTITLE_CONTAINERS, VIDEO_CONTAINERS


def is_video(path: Path) -> bool:
    return path.suffix[1:] in VIDEO_CONTAINERS

def is_subtitle(path: Path) -> bool:
    return path.suffix[1:] in SUBTITLE_CONTAINERS

def _file_traverse(target:Path)->Iterator[Path]:
    if target.is_dir():
        yield from (f for f in target.glob("**/*")
                    if Path.is_file and not any(part.startswith('.') for part in f.parts))
    else:
        yield target

def traverse(*args:Path)->Iterator[Path]:
    """
    find all media file in args

    """
    return (target
            for target in chain(*(_file_traverse(f) for f in args))
            if is_video(target)
            )
