from __future__ import annotations

import os
import pprint
import tempfile
from abc import ABC, abstractmethod
from dataclasses import replace as data_replace
from enum import Enum
from functools import partial
from pathlib import Path
from typing import Callable, get_type_hints

import requests
from teletype.components import ChoiceHelper, SelectOne
from teletype.io import style_input
from typing_inspect import Generic, TypeVar

import peets.naming as naming
from peets.entities import MediaEntity, MediaFileType, Movie, TvShow
from peets.merger import replace
from peets.nfo import generate_nfo
from peets.scraper import artwork, metadata

pp = pprint.PrettyPrinter(indent=2)

test: str = 1


class Action(Enum):
    # NO_ACTION = 0
    NEXT = 1
    QUIT = 3


OpResult = MediaEntity | dict | Action
OpCallable = Callable[[MediaEntity], OpResult]
Op = tuple[str, OpCallable]

R = TypeVar("R")
T = TypeVar("T", bound=MediaEntity)


class MediaUI(ABC, Generic[T]):
    def __init__(self) -> None:
        self.abc = "abc"

    @abstractmethod
    def brief(self, media: T):
        pass

    @abstractmethod
    def edit_ops(self, media: T) -> list[Op]:
        pass


_ui_maps: dict[str, MediaUI] = {}


class MovieUI(MediaUI[Movie]):
    def brief(self, media: Movie):
        print(f"Type: {type(media).__name__}")
        print(f"Title: {media.title}")
        print(f"Year: {media.year}")
        for k, v in media.ids.items():
            print(f"{k}: {v}")
        for mf in media.media_files:
            print(f"{mf[0].name}: {mf[1]}")

    def edit_ops(self, media: Movie) -> list[tuple[str, str, Callable]]:
        return [
            ("edit name", "n", partial(_modify, attr="title")),
            ("edit year", "y", partial(_modify, attr="year")),
        ]


class TvShowUI(MediaUI[TvShow]):
    def brief(self, media: TvShow):
        print(f"Type: {type(media).__name__}")
        print(f"Title: {media.title}")
        print(f"Year: {media.year}")
        for k, v in media.ids.items():
            print(f"{k}: {v}")
        for mf in media.media_files:
            print(f"{mf[0].name}: {mf[1]}")
        for e in media.episodes:
            print(f"S{e.season:02d}E{e.episode:02d}")


def interact(media: MediaEntity, lib_path: Path, naming_style: str) -> Action:
    _brief(media)
    ops = [
        ("search", _search),
        ("fetch by Id", do_fill),
        ("edit...", do_edit),
        ("view...", do_view),
        ("detail", lambda media: pp.pprint(media.__dict__)),
        ("process", partial(do_process, lib_path=lib_path, naming_style=naming_style)),
        ("skip", Action.NEXT),
    ]
    ops = _parse_ops(ops)
    while True:
        try:
            pick = _hint(ops)
            result = pick(media) if isinstance(pick, Callable) else pick
            match result:
                case MediaEntity():
                    media = result
                    _brief(media)
                case dict():
                    media = replace(media, **result)
                    _brief(media)
                case Action.NEXT | Action.QUIT:
                    return result
        except KeyboardInterrupt:
            return Action.QUIT


def _parse_ops(ops: list[Op]) -> list[ChoiceHelper[OpCallable]]:
    return _to_choices(ops)


def _to_choices(ops: list[tuple[str, R]]) -> list[ChoiceHelper[R]]:
    """
    1. 选择快捷键，按 op 顺序应用如下优先级：
     - 第一个大写字母
     - 第一个字母
     - 第 n 个字母
     - 第一个大写字母/第一个字母的字母表顺序
     - 不支持快捷键
    """
    ...

    def _first_key(s) -> str:
        try:
            return next(c for c in s if c.isupper())
        except StopIteration:
            return next(c for c in s if c.isalpha())

    keys = []
    for op in ops:
        dsc = op[0]
        best = _first_key(dsc).lower()
        if best not in keys:
            keys.append(best)
            continue
        else:
            # 第一个  alpha 可能被比较两次
            try:
                keys.append(next(c for c in dsc if c.isalpha() and c not in keys))
                continue
            except StopIteration:
                pass
        # 字母表顺序
        for i in range(ord(best) + 1, ord("z") + 1):
            c = chr(i)
            if c not in keys:
                keys.append(c)
                break

    return [
        ChoiceHelper(
            v[1], label=v[0], mnemonic_style=["green", "bold", "underline"], mnemonic=k
        )
        for k, v in zip(keys, ops)
    ]


def _hint(ops: list[ChoiceHelper]):
    width = os.get_terminal_size().columns
    label = "Action"
    padding = 1
    margin = 0
    leading = int((width - len(label)) / 2 - padding - margin)
    header = (
        " " * margin
        + "=" * leading
        + " " * padding
        + label
        + " " * padding
        + "=" * leading
        + " " * margin
    )
    print()
    print(header)

    return SelectOne(ops).prompt()


def _modify(media: T, attr: str) -> T:
    promt = "".join(ele.title() for ele in attr.split("_"))
    value = style_input(f"{promt}:", style=["blue", "bold"])
    # FIXME
    type_ = get_type_hints(type(media))[attr]
    return replace(media, {attr: type_(value)})


def do_edit(media: T) -> T:
    ops = {}
    return media


def _brief(media: MediaEntity):
    ui = _ui_maps[type(media).__name__]
    ui.brief(media)


def do_fill(media: T) -> T:
    id_ = style_input("tmdb id:", style=["blue", "bold"])
    scraper = metadata(media)
    new_ = scraper.apply(media, id_=int(id_))
    scraper = artwork(media)
    return scraper.apply(new_)


def _search(media: MediaEntity):
    scrapers = metadata(media)
    if len(scrapers) > 1:
        choices = [
            ChoiceHelper(
                s, label=f"{s.title} - {s.year} - {s.rank}({s.id_})", style="bold"
            )
            for s in scrapers
        ]

    result = scraper.search(media)
    if result:
        choices = [
            ChoiceHelper(
                s, label=f"{s.title} - {s.year} - {s.rank}({s.id_})", style="bold"
            )
            for s in result
        ]
        pick = SelectOne(choices).prompt()
        print("Fetching...")
        new_ = scraper.apply(media, id_=pick.id_)
        scraper = artwork(media)
        return scraper.apply(new_)
    else:
        print("Not Found!")


def do_process(media: MediaEntity, lib_path: Path, naming_style: str):
    # fetch online media file
    parsed: tuple[MediaFileType, Path] = [
        (t, _make_sure_media_file(t, uri))
        for t, uri in media.artwork_url_map.items()
        if not media.has_media_file(t)
    ]

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


def _make_sure_media_file(type_: MediaFileType, uri: str | Path) -> Path:
    print(f"fetching {uri} as {type_.name}")
    if type(uri) is str and uri.startswith("http"):
        uri = Path(_download_to_tmp(uri))
    return uri


def _download_to_tmp(url) -> str:
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        # FIXME 从 url 或者 content-type 获取后缀
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"save to {f.name}")
    return f.name
