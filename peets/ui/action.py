from __future__ import annotations

import os
import readline
import tempfile
from abc import ABC, abstractmethod
from dataclasses import replace as data_replace
from enum import Enum
from functools import partial, chain
from itertools import groupby
from pathlib import Path
from typing import Callable, Generic, Iterable, TypeVar, get_type_hints

import requests
from teletype.components import ChoiceHelper, SelectOne
from teletype.io import get_key, style_input
from operator import attrgetter

from peets.entities import MediaEntity, MediaFileType, Movie, TvShow, TvShowEpisode
from peets.merger import replace
from peets.scraper import MetadataProvider, Provider
from peets.util.type_utils import check_iterable_type, is_assignable


class Action(Enum):
    # NO_ACTION = 0
    NEXT = 1
    QUIT = 3


OpResult = MediaEntity | dict | Action | None

OpCallable = Callable[[MediaEntity], OpResult]

Op = tuple[str, OpCallable | OpResult]
R = TypeVar("R")

T = TypeVar("T", bound=MediaEntity)


class MediaUI(ABC, Generic[T]):
    @abstractmethod
    def brief(self, media: T):
        pass

    @abstractmethod
    def ops(self) -> list[Op]:
        pass


class MovieUI(MediaUI[Movie]):
    def brief(self, media: Movie):
        print(f"Type: {type(media).__name__}")
        print(f"Title: {media.title}")
        print(f"Year: {media.year}")
        for k, v in media.ids.items():
            print(f"{k}: {v}")
        for mf in media.media_files:
            print(f"{mf[0].name}: {mf[1]}")

    def ops(self) -> list[Op]:
        return [
            search_op(),
            fill_op(),
            edit_op([modify_op("title"), modify_op("year")]),
            view_op()
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

        for (k, v) in meida.episode_groupby_season():
            e_list = ",".join([str(e.episode) for e in v])
            print(f"Season {k}({len(e_list)}): {e_list}")


    def ops(self) -> list[Op]:
        return [
            search_op(),
            fill_op(),
            edit_op([modify_op("title"), modify_op("year")]),
            view_op()
        ]

    def list_episode(media: TvShow):
        groups = meida.episode_groupby_season()

        all_ = [("All", list(chain(*groups.values())))]
        ops = [(f"Season {k}", v)  for (k, v) in groups] + all_
        pick = _select(ops, "Season")



class TvShowEpisodeUI(MediaUI[TvShowEpisode]):
    def brief(self, media: TvShowEpisode):
        print(f"Type: {type(media).__name__}")
        print(f"Title: {media.title}")
        print(f"Episode: {media.episode}")
        print(f"Season: {media.season}")
        for k, v in media.ids.items():
            print(f"{k}: {v}")
        for mf in media.media_files:
            print(f"{mf[0].name}: {mf[1]}")


    def ops(self) -> list[Op]:
        return [
            edit_op([modify_op("title"), modify_op("episode"), modify_op("season")]),
            view_op()
        ]

def parse_ops(ops: list[Op]) -> list[ChoiceHelper[OpCallable | OpResult]]:
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
        found = False
        for i in range(ord(best) + 1, ord("z") + 1):
            c = chr(i)
            if c not in keys:
                keys.append(c)
                found = True
                break
        # 找不到的占位符
        if not found:
            keys.append(" ")

    return [
        ChoiceHelper(
            v[1], label=v[0], mnemonic_style=["green", "bold", "underline"], mnemonic=k
        )
        for k, v in zip(keys, ops)
    ]



def _select(media: T, ops: list[Op], label: str) -> T:
    """
    生成一个可返回的选择菜单
    """
    ops_ = parse_ops(ops + [("Back", Action.QUIT)])
    while True:
        pick = hint(ops_, label)
        result = pick(media) if callable(pick) else pick
        match result:
            case MediaEntity():
                media = result
            case dict():
                media = replace(media, **result)
            case Action.QUIT:
                return media

def hint(ops: list[ChoiceHelper], label: str) -> Any:
    width = os.get_terminal_size().columns
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

    return SelectOne(ops).prompt("=" * width)




def _pick_metadata_scraper(media: T) -> MetadataProvider[T]:
    scrapers = manager.metadata(media)
    if len(scrapers) > 1:
        choices = [ChoiceHelper(s, label=f"{type(s)}", style="bold") for s in scrapers]
        return SelectOne(choices).prompt()
    else:
        return scrapers[0]


def _pick_artwork_scraper(media: T) -> Provider[T]:
    scrapers = manager.artwork(media)
    if len(scrapers) > 1:
        choices = [ChoiceHelper(s, label=f"{type(s)}", style="bold") for s in scrapers]
        return SelectOne(choices).prompt()
    else:
        return scrapers[0]


def fill_op() -> Op:
    def do_fill(media: T) -> T:
        scraper = _pick_metadata_scraper(media)
        id_ = style_input(f"{type(scraper)} id:", style=["blue", "bold"])
        new_ = scraper.apply(media, id_=int(id_))
        scraper = _pick_metadata_scraper(media)
        return scraper.apply(new_)

    return  ("fetch by Id", do_fill)

def search_op() -> Op:
    def do_search(media: MediaEntity):
        scraper = _pick_metadata_scraper(media)
        result = scraper.search(media)
        if result:
            choices = [
                ChoiceHelper(
                    s, label=f"{s.title} - {s.year} - {s.rank}({s.id_})", style="bold"
                )
                for s in result
            ]
            choices += _to_choices([("Cancel", Action.QUIT)])
            pick = SelectOne(choices).prompt()
            if pick == Action.QUIT:
                print("Cancel")
            else:
                print("Fetching...")
                return scraper.apply(media, id_=pick.id_)
        else:
            print("Not Found!")

    return ("Search", do_search)


def modify_op(attr: str) -> Op:
    def _modify(media: T, attr: str) -> T:
        promt = "".join(ele.title() for ele in attr.split("_"))
        readline.set_startup_hook(lambda: readline.insert_text(str(getattr(media, attr))))
        try:
            value = style_input(f"{promt}:", style=["blue", "bold"])
        finally:
            readline.set_startup_hook()
        # FIXME
        type_ = get_type_hints(type(media))[attr]
        return replace(media, {attr: type_(value)})

    return (f"edit {attr.capitalize()}", partial(_modify, attr=attr))


def edit_op(extends: list[Op] = []) -> Op:
    def do_edit(media: T) -> T:
        return _select(media, extends + [("edit by Field", _edit_by_field)], "Edit")

    return ("Edit...", do_edit)

def _edit_by_field(media: T) -> T:
    def _type_filter(type_: type) -> bool:
        return type_ in [bool, int, float, str]

    fs = [f for f in get_type_hints(type(media)).items() if _type_filter(f[1])]

    def _edit_field(media: T, attr: Field) -> T:
        # TODO 检查是否是 MediaEntity 的子类或集合
        type_ = attr[1]
        value = getattr(media, attr[0])
        if is_assignable(type_, MediaEntity):
            return do_edit(value)
        elif is_assignable(type_, Iterable) and check_iterable_type(value, MediaEntity):
            return _select([(m.title, do_view) for m in value], "Select Media")
        else:
            return _modify(media, attr[0])

    return _select(
        media, [(f[0], partial(_edit_field, attr=f)) for f in fs], "View by Field"
    )

def view_op():
    def do_view(media: T):
        _select(
            media,
            [
                ("brief", _brief),
                ("detail", lambda media: pp.pprint(media.__dict__)),
                ("view by Field", _view_by_field),
            ],
            "View",
        )

    return ("View...", do_view)


def _view_by_field(media: T):
    def _type_filter(type_: type) -> bool:
        return type_ in [bool, int, float, str, list, dict, tuple]

    fs = [f for f in get_type_hints(type(media)).items() if _type_filter(f[1])]

    def _print_field(media: T, attr: tuple[str, type]):
        # TODO 检查是否是 MediaEntity 的子类或集合
        type_ = attr[1]
        value = getattr(media, attr[0])
        if is_assignable(type_, MediaEntity):
            do_view(value)
        elif is_assignable(type_, Iterable) and check_iterable_type(value, MediaEntity):
            _select([(m.title, do_view) for m in value], "Select Media")
        else:
            print(f"{attr[0]}: {value}")
            get_key()

    _select(media, [(f[0], partial(_print_field, attr=f)) for f in fs], "View by Field")
