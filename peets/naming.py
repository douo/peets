from functools import partial
import stat
from os import chmod
from pathlib import Path
from shutil import copy

from reflink import reflink
from peets.config import Config, Op

from peets.entities import MediaEntity, MediaFileType
from peets.library import Library



def _naming(media: MediaEntity, template="{title}({year})") -> str:
    return template.format(**media.__dict__, type=type_(media))


def type_(media: MediaEntity) -> str:
    return type(media).__name__.lower()



def _media_file_simple(type_: MediaFileType) -> str:
    if type_ is MediaFileType.NFO:
        return "movie"
    elif type_.is_graph():
        return type_.name.lower()
    else:
        return type_.name.lower()  # FIXME


def _media_file(type_: MediaFileType, prefix: str) -> str:
    if type_ is MediaFileType.NFO:
        return prefix
    elif type_.is_graph():
        return f"{prefix}-{type_.name.lower()}"
    else:
        return type_.name.lower()  # FIXME


def _op(src: Path, dst: Path, op: Op):
    if op == Op.Reflink:
        reflink(str(src), str(dst))
    elif op == Op.Copy:
        copy(src, dst)
    else:
        raise ValueError(f"{op=} is not support yet.")

    return (src, op, dst)

def do_copy(media: MediaEntity, lib: Library):
    lib_path = lib.path
    config = lib.config

    # create folder
    naming = _naming(media, template=config.naming_template)
    _tmp = lib_path.joinpath(naming)
    parent = _tmp.parent
    prefix = _tmp.name
    parent.mkdir(parents=True)

    # main video
    main_video_path = media.main_video()
    new_path = parent.joinpath(f"{prefix}{main_video_path.suffix}")

    lib.record(*_op(main_video_path, new_path, config.op))

    mod = stat.S_IMODE(new_path.stat().st_mode)
    # other media file

    simple = "simple" == config.media_file_naming_style
    media_file_selected = _media_file_simple if simple else partial(_media_file, prefix=prefix)
    for t, p in media.media_files:
        if p is not main_video_path:
            n = parent.joinpath(f"{media_file_selected(t)}{p.suffix}")
            lib.record(*_op(p, n, Op.Copy))  # TODO performance matter
            # 与主视频文件的权限保持一致
            chmod(n, mod)
