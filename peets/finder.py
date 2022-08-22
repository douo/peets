from pathlib import Path
from typing import Iterator
from itertools import chain


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


def _movie_filter(target:Path)->bool:
    return target.suffix[1:] in MOVIE_CONTAINERS

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
            if _movie_filter(target)
            )
