from __future__ import annotations

import os
import readline
from abc import ABC, abstractmethod
from enum import Enum
from functools import partial
from itertools import chain
from typing import Callable, Generic, Iterable, TypeVar, get_type_hints, TYPE_CHECKING

from teletype.components import ChoiceHelper, SelectMany, SelectOne
from teletype.io import get_key, style_input

from peets.entities import MediaEntity, Movie, TvShow, TvShowEpisode

from peets.merger import replace
from peets.scraper import MetadataProvider, Provider
from peets.util.type_utils import check_iterable_type, is_assignable


if TYPE_CHECKING:
    from peets.library import Library


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

    def __init__(self, lib:Lirary):
        self.lib = lib

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
            search_op(self.lib),
            fill_op(self.lib),
            edit_op([modify_op("title"), modify_op("year")]),
            view_op(),
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

        for (k, v) in media.episode_groupby_season():
            e_list = [str(e.episode) for e in v]
            text = ",".join(e_list)
            print(f"Season {k}({len(e_list)}): {text}")

    def ops(self) -> list[Op]:
        return [
            search_op(self.lib),
            fill_op(self.lib),
            edit_op([modify_op("title"), modify_op("year")]),
            view_op(),
            ("List...", list_season),
        ]


def list_season(media: TvShow) -> TvShow:
    def _ops(media: TvShow) -> list[Op]:
        seasons = [k for (k, _) in media.episode_groupby_season()]
        all_ = [("All", list_episode("all"))]
        return [(f"Season {k}", list_episode(k)) for k in seasons] + all_

    return select(media, _ops, "Season")


def list_episode(season_tag: int | str):
    def _inner(media: TvShow) -> TvShow:
        def _ops(media: TvShow) -> list[Op]:
            groups = media.episode_groupby_season()
            if season_tag == "all":
                episodes = list(chain(*[list(v) for (_, v) in groups]))
            else:
                episodes = next(v for (k, v) in groups if k == season_tag)
            ops = [
                (f"S{e.season}E{e.episode}:{e.main_video().name}", view_episode(e))
                for e in episodes
            ]
            ops.append(("batch edit Season...", batch_edit_season(season_tag)))
            return ops

        return select(media, _ops, f"Season {season_tag}")

    return _inner


def batch_edit_season(season_tag: int | str):
    def _inner(media: TvShow) -> TvShow:
        def _ops(media: TvShow) -> list[Op]:
            groups = media.episode_groupby_season()
            if season_tag == "all":
                episodes = list(chain(*[list(v) for (_, v) in groups]))
            else:
                episodes = next(v for (k, v) in groups if k == season_tag)
            return [
                (f"S{e.season}E{e.episode}:{e.main_video().name}", e) for e in episodes
            ]

        while True:
            pick = hint(parse_ops(_ops(media)), "Batch Edit Season", select_many=True)
            if pick:
                value = style_input(f"Season:", style=["blue", "bold"])
                new_es = [
                    replace(e, {"season": int(value)}) if e in pick else e
                    for e in media.episodes
                ]
                media = replace(media, {"episodes": new_es})
            else:
                return media

    return _inner


def view_episode(episode: TvShowEpisode):
    def _inner(tvshow: TvShow) -> TvShow:
        def brief(media: TvShowEpisode):
            print(f"Type: {type(media).__name__}")
            print(f"Title: {media.title}")
            print(f"Episode: {media.episode}")
            print(f"Season: {media.season}")
            for k, v in media.ids.items():
                print(f"{k}: {v}")
            for mf in media.media_files:
                print(f"{mf[0].name}: {mf[1]}")

        ops = [edit_op([modify_op("title"), modify_op("episode"), modify_op("season")]),
               view_op(),
               ]
        new_e = select(episode, ops, "Action", brief = brief)
        if new_e != episode:
            new_es = [(new_e if e.dbid == new_e.dbid else e) for e in tvshow.episodes]
            return replace(tvshow, {"episodes": new_es})
        else:
            return tvshow

    return _inner


def parse_ops(
    ops: list[Op], last_first=False
) -> list[ChoiceHelper[OpCallable | OpResult]]:
    return _to_choices(ops, last_first)


def _to_choices(ops: list[tuple[str, R]], last_first=False) -> list[ChoiceHelper[R]]:
    """
    1. 自动生成快捷键，按 op 顺序应用如下优先级：
     - 第一个大写字母
     - 第一个字母
     - 第 n 个字母
     - 第一个大写字母/第一个字母的字母表顺序
     - 不支持快捷键
    """

    def _first_key(s) -> str:
        try:
            return next(c.lower() for c in s if c.isupper())
        except StopIteration:
            return next(c for c in s if c.isalpha())

    def _generate_mnemonic(
        ops: list[tuple[str, R]], exclude=[]
    ) -> list[ChoiceHelper[R]]:
        keys = list(exclude)
        for op in ops:
            dsc = op[0]
            best = _first_key(dsc)
            if best not in keys:
                keys.append(best)
                continue
            else:
                dsc = dsc.lower()
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
                keys.append("\0")

        return keys[len(exclude) :]

    last_op = ops[-1:] if last_first else []
    _ops = ops[:-1] if last_first else ops
    last_key = _generate_mnemonic(last_op)
    keys = _generate_mnemonic(_ops, last_key) + last_key

    return [
        ChoiceHelper(
            v[1], label=v[0], mnemonic_style=["green", "bold", "underline"], mnemonic=k
        )
        for k, v in zip(keys, ops)
    ]


def select(
    media: T,
    ops: list[Op] | Callable[[T], list[Op]],
    label: str,
    quit_label: str | None = "Back",
    brief: Callable | None = None,
) -> T:
    """
    生成一个可返回的选择菜单
    """

    def _build_ops() -> list[Op]:
        if callable(ops):
            _ops = ops(media)
        else:
            _ops = ops
        if quit_label:
            _ops = _ops + [(quit_label, Action.QUIT)]

        return parse_ops(_ops, last_first=bool(quit_label))

    if brief:
        brief(media)
    while True:
        pick = hint(_build_ops(), label)
        result = pick(media) if callable(pick) else pick
        match result:
            case MediaEntity():
                media = result
                if brief:
                    brief(media)
            case dict():
                media = replace(media, **result)
                if brief:
                    brief(media)
            case Action.NEXT | Action.QUIT:
                return media
            case _:
                if brief:
                    brief(media)


def hint(ops: list[ChoiceHelper], label: str, select_many=False) -> Any:
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
    if select_many:
        return SelectMany(ops).prompt("=" * width)
    else:
        return SelectOne(ops).prompt("=" * width)


def _pick_metadata_scraper(media: T, lib: Library) -> MetadataProvider[T]:
    scrapers = lib.manager.metadata(media)
    if len(scrapers) > 1:
        choices = [ChoiceHelper(s, label=f"{type(s)}", style="bold") for s in scrapers]
        return SelectOne(choices).prompt()
    else:
        return scrapers[0]


def _pick_artwork_scraper(media: T, lib: Library) -> Provider[T]:
    scrapers = lib.manager.artwork(media)
    if len(scrapers) > 1:
        choices = [ChoiceHelper(s, label=f"{type(s)}", style="bold") for s in scrapers]
        return SelectOne(choices).prompt()
    else:
        return scrapers[0]


def fill_op(lib: Library) -> Op:
    def do_fill(media: T) -> T:
        scraper = _pick_metadata_scraper(media, lib)
        id_ = style_input(f"{type(scraper)} id:", style=["blue", "bold"])
        new_ = scraper.apply(media, id_=int(id_))
        scraper = _pick_metadata_scraper(media, lib)
        return scraper.apply(new_)

    return ("fetch by Id", do_fill)


def search_op(lib: Library) -> Op:
    def do_search(media: MediaEntity):
        scraper = _pick_metadata_scraper(media, lib)
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
        readline.set_startup_hook(
            lambda: readline.insert_text(str(getattr(media, attr)))
        )
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
        return select(media, extends + [("edit by Field", _edit_by_field)], "Edit")

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
            return select([(m.title, do_view) for m in value], "Select Media")
        else:
            return _modify(media, attr[0])

    return select(
        media, [(f[0], partial(_edit_field, attr=f)) for f in fs], "View by Field"
    )


def view_op():
    def do_view(media: T):
        select(
            media,
            [
                ("as Json", lambda m: print(m.to_json())),
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
            select([(m.title, do_view) for m in value], "Select Media")
        else:
            print(f"{attr[0]}: {value}")
            get_key()

    select(media, [(f[0], partial(_print_field, attr=f)) for f in fs], "View by Field")
