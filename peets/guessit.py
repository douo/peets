from pathlib import Path
from guessit.api import GuessItApi, merge_options
from guessit.rules import rebulk_builder
from guessit.rules.processors import Processors
from guessit.rules.properties.crc import guess_idnumber
from guessit.rules.properties.episode_title import POST_PROCESS, title_seps
from rebulk import CustomRule
from rebulk.match import Match
from peets.entities import MediaFileType, Movie, MediaEntity
from peets.error import UnknownMediaTypeError
from peets.merger import create
from peets.finder import  is_artwork_file, is_subtitle, is_video
from enum import Enum

import os
import regex
# use regex replace re
os.environ['REBULK_REGEX_ENABLED'] = '1'

class NonMedia(Enum):
    TRAILER = 1
    SAMPLE = 2


class _TittleSplitRule(CustomRule):
    priority = POST_PROCESS
    dependency = Processors
    def when(self, matches, context):
        title = matches.named('title')

        if title and len(title) > 0:
            title = title[0]
            value = title.value
            # 如果开头匹配 cjk 与标点，后面还有其他字符，则认为是 =翻译名Origin Name= 这样的形式
            # https://www.compart.com/en/unicode/scripts
            cjk =  regex.compile(r"^[\p{Han}\p{Hiragana}\p{Katakana}[\p{Po}]]+", regex.V1)

            m = cjk.search(value)
            if m and len(m) == 1 and m.end() < len(value):
                print(m.end())
                return (title, m)

    def then(self, matches, when_response, context):
        title, m = when_response
        _start = title.start
        _end = title.end
        origin = title.value[m.end()+1:]
        title.end = m.end()
        title.value = m.group()
        matches.append(Match(m.end()+1, _end, name='original_title', value=origin))


# FIXME multiple file movie
def create_entity(path: Path)-> MediaEntity | NonMedia:
    """
    one file one movie
    """
    # 只能处理视频文件
    api = GuessItApi()
    def custom_rebulk(config):
        rebulk = rebulk_builder(config)
        rebulk.rules(_TittleSplitRule)
        return rebulk

    config = api.configure(options = {}, rules_builder= custom_rebulk,
                           sanitize_options=False)
    options = merge_options(config, {})

    matches = api.rebulk.matches(str(path), options)

    guess = matches.to_dict()

    # 非正片会被忽略，后续会通过关联的正片找到
    # 如果找不到，说明是独立的影片，是否没有入库的意义

    match guess:
        case {"other" : "Trailer"} | {"other" : ["Trailer", *_]} :
            return NonMedia.TRAILER
        case {"other" : "Sample"} | {"other" : ["Sample", *_]} :
            return NonMedia.SAMPLE
        case {"type": "movie"}:
            return _create_movie(guess, path)
        case _:
            raise UnknownMediaTypeError(guess)

def parse_mediafile_type(path: Path) -> MediaFileType:
    if is_video(path):
        if MediaFileType.TRAILER.name in path.stem:
            return MediaFileType.TRAILER
        elif MediaFileType.SAMPLE.name in path.stem:
            return MediaFileType.SAMPLE
        else:
            return MediaFileType.VIDEO
    if is_subtitle(path):
        return MediaFileType.SUBTITLE
    if is_artwork_file(path):
        for t in MediaFileType.graph_type():
            if t.name.lower() in path.stem.lower():
                return t
    if "nfo" == path.suffix[1:]:
        return MediaFileType.NFO
    #TODO other type
    return MediaFileType.UNKNOWN

def _create_movie(guess: dict, path: Path) -> Movie: # type: ignore
    # TODO 暂时只处理同级文件
    mfs = [(parse_mediafile_type(child), child) for child in path.parent.iterdir() if child != path]
    mfs = [c for c in mfs if c[0] is not MediaFileType.UNKNOWN]
    # 如果有存在 trailer 或者 sample 之外的视频存在，则认为目录存放有多个视频文件
    multi_movie_dir = bool(mfs) and MediaFileType.VIDEO in next(zip(*mfs))
    # 如果是 mmd 则 mediafile 中含有当前文件名的才能被认为是属于当前的资源
    if multi_movie_dir:
        mfs = [c for c in mfs if path.stem in c[1].stem and c[0] != MediaFileType.VIDEO]
        guess["multi_movie_dir"] = True

    mfs.append((MediaFileType.VIDEO, path))
    guess["media_files"] = mfs
    guess['original_filename'] = path.name

    return create(Movie, guess)
