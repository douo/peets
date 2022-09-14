from pathlib import Path
from shutil import copy
from reflink import reflink, supported_at
from peets.entities import MediaEntity, MediaFileType


def _naming(media: MediaEntity, template="{title}({year})") -> str:
    return template.format(**media.__dict__)


def type_(media: MediaEntity) -> str:
    return type(media).__name__.lower()

def folder(media: MediaEntity) -> str:
    return _naming(media, "{title} ({year})")

def main_video(media: MediaEntity) -> str:
    return _naming(media, "{title} ({year}) {screen_size} {audio_codec}")

def media_file_simple(media: MediaEntity, type_: MediaFileType, path: Path) -> str:
    if type_ is MediaFileType.NFO:
        return "movie"
    elif type_.is_graph():
        return type_.name.lower()
    else:
        return type_.name.lower() # FIXME

def media_file(media: MediaEntity, type_: MediaFileType, path: Path) -> str:
    if type_ is MediaFileType.NFO:
        return main_video(media)
    elif type_.is_graph():
        return f"{main_video(media)}-{type_.name.lower()}"
    else:
        return type_.name.lower() # FIXME


def do_copy(media: MediaEntity, lib_path: Path, simple=True):
    # create folder
    parent = lib_path.joinpath(type_(media), folder(media))
    parent.mkdir(parents=True)

    # main video
    main_video_path = media.main_video()
    new_path= parent.joinpath(f"{main_video(media)}{main_video_path.suffix}")

    if main_video_path.is_relative_to(lib_path):
        print(f"WARING: {main_video_path} is relative to {lib_path}")
    #FIXME check at init
    if supported_at(lib_path):
        print(f"reflink {str(main_video_path)} to {str(new_path)}")
        reflink(str(main_video_path), str(new_path))
    else:
        copy(main_video_path, new_path)

    # other media file
    for t, p  in media.media_files:
        media_file_selected = media_file_simple if simple else  media_file
        if p is not main_video_path:
            n = parent.joinpath(f"{media_file_selected(media, t, p)}{p.suffix}")
            print(f"copy {str(p)} to {str(n)}")
            copy(p, n)
