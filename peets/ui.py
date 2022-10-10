from typing import Any, Callable, get_type_hints
from pathlib import Path
from dataclasses import dataclass, replace as data_replace
from functools import partial, partialmethod
from enum import Enum
from pickle import NEXT_BUFFER

from teletype.components import ChoiceHelper, SelectOne, SelectApproval
from teletype.io import get_key, style_format, style_print, strip_format, style_input
from tmdbsimple import Account
from typing_inspect import TypeVar

from peets.entities import MediaArtworkType, MediaEntity, MediaFileType, TvShow
from peets.merger import replace
from peets.nfo  import generate_nfo
import peets.naming as naming

import pprint

from peets.scraper import artwork, metadata
pp = pprint.PrettyPrinter(indent=2)

@dataclass
class MediaVO:
    name: str
    year: str
    id_: str

class Action(Enum):
    # NO_ACTION = 0
    NEXT = 1
    QUIT = 3

T = TypeVar("T", bound=MediaEntity)

def interact(media: MediaEntity, lib_path: Path, naming_style: str):
    brief(media)
    ops = {
        "lf": ("search", "enter", do_search),
        "i": ("fetch by id", "i", do_fill),
        "n": ("edit name", "n", partial(modify,attr="title")),
        "y": ("edit year", "y", partial(modify, attr="year")),
        "d": ("detail", "d", lambda media: pp.pprint(media.__dict__)),
        "p": ("process", "p", partial(do_process, lib_path=lib_path, naming_style=naming_style)),
        "j": ("skip", "j", Action.NEXT)
    }
    hint = lambda : style_print(", ".join([f"{label} ({key})" for label, key, _ in ops.values()]),
                                style=["green", "bold"])
    hint()
    while sel := get_key() :
        print(sel)
        if sel in ops.keys():
            result = ops[sel][2]
            result = result(media) if isinstance(result, Callable) else result
            match result:
                case MediaEntity():
                    media = result
                    brief(media)
                case dict():
                    media = replace(media, **result)
                    brief(media)
                case Action.NEXT | Action.QUIT:
                    return result

        elif sel in ("ctrl-c", "ctrl-z", "escape"):
            return Action.QUIT
        else:
            pass
        hint()

def modify(media: T, attr: str) -> T:
    promt = "".join(ele.title() for ele in attr.split('_'))
    value = style_input(f"{promt}:", style=["blue", "bold"])
    #FIXME
    type_ = get_type_hints(type(media))[attr]
    return replace(media, {attr: type_(value)})

def brief(media: MediaEntity):
    print(f"Type: {type(media).__name__}")
    print(f"Title: {media.title}")
    print(f"Year: {media.year}")
    for k, v in media.ids.items():
        print(f"{k}: {v}")
    for mf in media.media_files:
        print(f"{mf[0].name}: {mf[1]}")

    if isinstance(media, TvShow):
        for e in media.episodes:
            print(f"S{e.season:02d}E{e.episode:02d}")

def do_fill(media: T) -> T:
    id_  = style_input("tmdb id:", style=["blue", "bold"])
    scraper = metadata(media)
    new_ = scraper.apply(media, id_ = int(id_))
    scraper = artwork(media)
    return scraper.apply(new_)

def do_search(media: MediaEntity):
    print("Searching...")
    scraper = metadata(media)
    result = scraper.search(media)
    if result:
        choices = [ChoiceHelper(
            s,
            label= f"{s.title} - {s.year} - {s.rank}({s.id_})",
            style="bold"
        ) for s in result]
        pick =  SelectOne(choices).prompt()
        print("Fetching...")
        new_ =  scraper.apply(media, id_ = pick.id_)
        scraper = artwork(media)
        return scraper.apply(new_)
    else:
        print("Not Found!")


import tempfile

def do_process(media: MediaEntity, lib_path: Path, naming_style: str):
    # fetch online media file
    parsed: tuple[MediaFileType, Path] = [(t, _make_sure_media_file(t, uri)) for t, uri in media.artwork_url_map.items() if not media.has_media_file(t)]

    if not media.has_media_file(MediaFileType.NFO):
        with tempfile.NamedTemporaryFile(suffix=".nfo", delete=False) as f:
            nfo = generate_nfo(media)
            f.write(nfo)
            print(f"parsing nfo to {f.name}")

        parsed.append((MediaFileType.NFO, Path(f.name)))
    media = data_replace(media, media_files=media.media_files + parsed)
    brief(media)
    naming.do_copy(media, lib_path, naming_style)
    return Action.NEXT

def _make_sure_media_file(type_: MediaFileType, uri: str | Path) ->  Path:
    print(f"fetching {uri} as {type_.name}")
    if type(uri) is str and uri.startswith("http"):
        uri = Path(_download_to_tmp(uri))
    return uri


import requests
def _download_to_tmp(url) -> str:
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        # FIXME 从 url 或者 content-type 获取后缀
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"save to {f.name}")
    return f.name
