from pathlib import Path
from dataclasses import replace
from pprint import pprint as pp
from typing import Any, TypeVar
from guessit.api import GuessItApi, guessit, merge_options
from guessit.rules import rebulk_builder
from guessit.rules.processors import Processors
from guessit.rules.properties.audio_codec import audio_codec
from guessit.rules.properties.crc import guess_idnumber
from guessit.rules.properties.episode_title import POST_PROCESS, episode_title, title_seps
from guessit.rules.properties.episodes import episodes
from rebulk import CustomRule
from rebulk.match import Match
from peets.entities import MediaFileType, Movie, MediaEntity, TvShow, TvShowEpisode
from peets.error import UnknownMediaTypeError
from peets.merger import MapTable, create
from peets.finder import  is_artwork_file, is_subtitle, is_video, traverse
from enum import Enum



import os
import regex
# use regex replace re
os.environ['REBULK_REGEX_ENABLED'] = '1'

class NonMedia(Enum):
    TRAILER = 1
    SAMPLE = 2
    PROCESSED = 3

class _ProcessedException(Exception):
    pass

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
def create_entity(path: Path, processed: set = set())-> MediaEntity | NonMedia:
    """
    one file one movie
    """
    if path in processed:
        return NonMedia.PROCESSED

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
    try:
        match guess:
            case {"other" : "Trailer"} | {"other" : ["Trailer", *_]} :
                return NonMedia.TRAILER
            case {"other" : "Sample"} | {"other" : ["Sample", *_]} :
                return NonMedia.SAMPLE
            case {"type": "movie"}:
                return _create_movie(guess, path, processed)
            case {"type": "episode"}:
                return _create_tvshow(guess, path, processed)
            case _:
                raise UnknownMediaTypeError(guess)
    except _ProcessedException:
        return NonMedia.PROCESSED

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

def _create_movie(guess: dict, path: Path, processed: set) -> Movie: # type: ignore
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
    return _do_create(processed, path, Movie, guess)

def _create_tvshow(guess, path: Path, processed: set) -> TvShow:
    episode_guess = guess
    # 预设可能目录情况有三种
    # 1. tvshow/season/episode
    # 2. tvshow/episode
    # 3. .../episode
    # TODO 相同剧集位于不同目录的情况 a/tvshow b/tvshow

    season_maybe = path.parent
    tvshow_maybe = path.parent.parent
    if tvshow_maybe in processed or season_maybe in processed:
        #当前剧集已被处理，抛出异常
        raise _ProcessedException()

    tvshow_guess = guessit(tvshow_maybe)
    tvshow_path = None
    if 'title' in tvshow_guess and tvshow_guess['title'] == episode_guess['title']:
        tvshow_path = tvshow_maybe
    else:
        tvshow_guess = guessit(season_maybe)
        if 'title' in tvshow_guess and tvshow_guess['title'] == episode_guess['title']:
            tvshow_path = season_maybe
        else:
            tvshow_guess = episode_guess

    if tvshow_path:
        return _create_tvshow_batch(tvshow_guess, tvshow_path, processed)
    else:
        # 情况3
        map_table:MapTable = [("audio_codec", "audio_codec", lambda a: "&".join(a))]
        tvshow_guess['episodes'] = [_do_create(processed, path, TvShowEpisode, episode_guess, map_table)]
        tvshow = create(TvShow, tvshow_guess, map_table)
        return tvshow

def _create_tvshow_batch(tvshow_guess, path: Path, processed: set) -> TvShow:
    processed.add(path)
    map_table:MapTable = [("audio_codec", "audio_codec", lambda a: "&".join(a))]
    episodes: list[TvShowEpisode] = [_do_create(processed, p, TvShowEpisode, guess, map_table)
                                     for p, guess in ((media, guessit(media)) for media in traverse(path))
                                     if guess["type"] == "episode" and ("other" not in guess or ("Trailer" not in guess["other"] and "Sample" not in guess["other"]))
    ]
    tvshow_guess['episodes'] = episodes
    tvshow = create(TvShow, tvshow_guess, map_table)
    return tvshow

T = TypeVar('T')
def _do_create(processed: set, path: Path, type_: type[T], addon: dict[str, Any], table: MapTable | None = None) -> T:
    addon['original_filename'] = path.name
    processed.add(path)
    return create(type_, addon, table)
