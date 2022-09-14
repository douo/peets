from pathlib import Path
from peets.entities import Movie
from peets.entities import MediaFileType, Movie

from peets.guessit import NonMedia, create_entity
from guessit import guessit

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
