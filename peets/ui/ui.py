from __future__ import annotations

import os
import readline
import tempfile
from dataclasses import replace as data_replace
from functools import cache, partial
from pathlib import Path
from typing import Any

import requests
from teletype.components import ChoiceHelper, SelectOne
from teletype.io import get_key, style_input

import peets.naming
from peets import manager
from peets.ui.action import T, Action, Op, MediaUI, parse_ops, select
from peets.entities import MediaEntity, MediaFileType
from peets.merger import replace
from peets.scraper import MetadataProvider, Provider
from peets.util.type_utils import check_iterable_type, is_assignable


@cache
def get_ui(type_: type[T]) -> MediaUI[Any]:
    return manager.get_ui(type_)()


def interact(media: MediaEntity, lib_path: Path, naming_style: str) -> Action:
    ui = get_ui(type(media))
    ops = ui.ops() + [
        (
                "Process",
                partial(_do_process, lib_path=lib_path, naming_style=naming_style),
            ),
            ("Skip", Action.NEXT),
        ]

    try:
        select(media, ops, "Action", None, ui)
    except KeyboardInterrupt:
        return Action.QUIT


def _do_process(media: MediaEntity, lib_path: Path, naming_style: str):
    # fetch online media file
    parsed: tuple[MediaFileType, Path] = [
        (t, _make_sure_media_file(t, uri))
        for t, uri in media.artwork_url_map.items()
        if not media.has_media_file(t)
    ]

    if not media.has_media_file(MediaFileType.NFO):
        with tempfile.NamedTemporaryFile(suffix=".nfo", delete=False) as f:
            nfo = manager.connectors(media)[0]  # FIXME
            f.write(nfo)
            print(f"parsing nfo to {f.name}")

        parsed.append((MediaFileType.NFO, Path(f.name)))
    media = data_replace(media, media_files=media.media_files + parsed)
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
    return f.name
    print(f"save to {f.name}")
    return f.name
    return f.name
