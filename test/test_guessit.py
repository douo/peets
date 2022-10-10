from pathlib import Path
from peets.entities import Movie, TvShow, TvShowEpisode
from peets.entities import MediaFileType, Movie

from peets.guessit import NonMedia, create_entity
from guessit import guessit
from peets.ui import interact

from util import create_file


def test_create_entity_with_movie(tmp_path):
    f = create_file("English.Name.2020.AAC-HE_LC_8ch.mkv", tmp_path)
    movie = create_entity(f)

    assert isinstance(movie, Movie)
    assert movie.title == "English Name"
    assert movie.year == 2020
    assert movie.original_filename == "English.Name.2020.AAC-HE_LC_8ch.mkv"
    assert movie.multi_movie_dir == False

    f = create_file("中文名.2021.UHD.BluRay.2160p.x265.10bit.HDR.mUHD-FRDS.mkv", tmp_path)
    movie = create_entity(f)
    assert isinstance(movie, Movie)
    assert movie.title == "中文名"
    assert movie.year == 2021
    assert movie.multi_movie_dir == True

    # 国内常用的命名规则
    f = create_file("中文名.English.Name.2021.UHD.BluRay.2160p.x265.10bit.HDR.mUHD-FRDS.mkv", tmp_path)
    movie = create_entity(f)
    assert isinstance(movie, Movie)
    assert movie.title == "中文名"
    assert movie.original_title == "English Name"
    assert movie.year == 2021
    assert movie.multi_movie_dir == True


def test_create_entity_with_movie_mediafile(tmp_path):
    files = [
        "movie with set graphics.avi",
        "movie with set graphics.nfo",
        "movieset-banner.jpg",
        "movieset-clearart.jpg",
        "movieset-clearlogo.jpg",
        "movieset-fanart.jpg",
        "movieset-logo.jpg",
        "movieset-poster.jpg"
    ]

    excepts = [
        MediaFileType.VIDEO,
        MediaFileType.NFO,
        MediaFileType.BANNER,
        MediaFileType.CLEARART,
        MediaFileType.CLEARLOGO,
        MediaFileType.FANART,
        MediaFileType.LOGO,
        MediaFileType.POSTER
    ]

    paths = [create_file(f, tmp_path) for f in files]

    movie = create_entity(paths[0])

    assert isinstance(movie, Movie)
    assert len(movie.media_files) == len(excepts)
    assert set([f[0] for f in movie.media_files]) == set(excepts)



def test_create_entity_with_trailer(tmp_path):
    f = create_file("Hight.Town.2020.AAC-HE_LC_8ch.trailer.mkv", tmp_path)
    assert NonMedia.TRAILER == create_entity(f)

    f = create_file("Hight.Town.2020.AAC-HE_LC_8ch.trailer_sample.mkv", tmp_path)
    assert NonMedia.TRAILER == create_entity(f)

def test_create_entity_with_sample(tmp_path):
    f = create_file("Hight.Town.2020.AAC-HE_LC_8ch.sample.mkv", tmp_path)
    assert NonMedia.SAMPLE == create_entity(f)


def test_create_tvshow(tmp_path):
    parent="Severance.S01.2160p.ATVP.WEB-DL.DDP5.1.Atmos.HEVC-TEPES"
    f1 = create_file("Severance.S01E01.Good.News.About.Hell.REPACK.2160p.ATVP.WEB-DL.DDP5.1.Atmos.HEVC-TEPES.mkv", tmp_path, parent=parent)
    f2 = create_file("Severance.S01E02.Good.News.About.Hell.REPACK.2160p.ATVP.WEB-DL.DDP5.1.Atmos.HEVC-TEPES.mkv", tmp_path, parent=parent)
    processed = set()
    m = create_entity(f1, processed)
    assert isinstance(m, TvShow)
    assert len(m.episodes) == 2
    assert all((e.season == 1 for e in m.episodes))

    # test processed
    assert f1 in processed and f2 in processed
    assert f1.parent in processed
    m = create_entity(f1, processed)
    assert m is NonMedia.PROCESSED

    f3 = create_file("Severance.S01E03.Good.News.About.Hell.REPACK.2160p.ATVP.WEB-DL.DDP5.1.Atmos.HEVC-TEPES.mkv", tmp_path, parent=parent)
    m = create_entity(f3, processed)
    # tvshow 目录不会重复处理
    assert m is NonMedia.PROCESSED

    # media file
    mf = [
        f"{f1.stem}.nfo",
        f"{f1.stem}-banner.jpg",
        f"{f1.stem}-clearart.jpg",
        f"{f1.stem}-clearlogo.jpg",
        f"{f1.stem}-fanart.jpg",
        f"{f1.stem}-logo.jpg",
        f"{f1.stem}-poster.jpg"
    ]

    excepts = [
        MediaFileType.NFO,
        MediaFileType.BANNER,
        MediaFileType.CLEARART,
        MediaFileType.CLEARLOGO,
        MediaFileType.FANART,
        MediaFileType.LOGO,
        MediaFileType.POSTER
    ]
    mf = [create_file(f, tmp_path, parent) for f in mf]

    m = create_entity(f1, set())
    assert isinstance(m, TvShow)
    assert len(m.episodes) == 3
    assert len(m.retrieve_episode(1,2).media_files) == 1
    assert len(m.retrieve_episode(1,3).media_files) == 1
    mf_episode = [mf[0] for mf in m.retrieve_episode(1,1).media_files if mf[0] != MediaFileType.VIDEO]
    assert set(mf_episode) == set(excepts)

    interact(m, tmp_path, "simple")
