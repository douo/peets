from shutil import move
from peets.naming import do_copy
from util import create_file
from peets.entities import MediaFileType, Movie
def test_do_copy_simple_naming(tmp_path):
    media_files = [
        (MediaFileType.VIDEO, "中文名.English.Name.2021.UHD.BluRay.2160p.x265.10bit.HDR.mUHD-FRDS.mkv"),
        (MediaFileType.NFO, "中文名.English.Name.2021.UHD.BluRay.2160p.x265.10bit.HDR.mUHD-FRDS.nfo"),
        (MediaFileType.BANNER, "中文名.English.Name.2021.UHD.BluRay.2160p.x265.10bit.HDR.mUHD-FRDS-banner.jpg"),
        (MediaFileType.POSTER, "中文名.English.Name.2021.UHD.BluRay.2160p.x265.10bit.HDR.mUHD-FRDS-poster.jpg")
    ]
    movie = Movie(
        title="Title",
        year=2022,
        audio_codec="AAC",
        screen_size="2160p",
        media_files=[(t, create_file(n, tmp_path, tmp_path.joinpath("src"))) for t, n in media_files]
    )

    lib_path = tmp_path.joinpath("dst")

    # simple
    do_copy(movie, lib_path, simple=True)

    parent = lib_path.joinpath("movie", "Title (2022)")
    assert parent.exists()
    assert set(f.name for f in parent.iterdir()) == set(["Title (2022) 2160p AAC.mkv",
                                                                             "movie.nfo",
                                                                             "poster.jpg",
                                                                             "banner.jpg"])

def test_do_copy(tmp_path):
    media_files = [
        (MediaFileType.VIDEO, "中文名.English.Name.2021.UHD.BluRay.2160p.x265.10bit.HDR.mUHD-FRDS.mkv"),
        (MediaFileType.NFO, "中文名.English.Name.2021.UHD.BluRay.2160p.x265.10bit.HDR.mUHD-FRDS.nfo"),
        (MediaFileType.BANNER, "中文名.English.Name.2021.UHD.BluRay.2160p.x265.10bit.HDR.mUHD-FRDS-banner.jpg"),
        (MediaFileType.POSTER, "中文名.English.Name.2021.UHD.BluRay.2160p.x265.10bit.HDR.mUHD-FRDS-poster.jpg")
    ]
    movie = Movie(
        title="Title",
        year=2022,
        audio_codec="AAC",
        screen_size="2160p",
        media_files=[(t, create_file(n, tmp_path, tmp_path.joinpath("src"))) for t, n in media_files]
    )

    lib_path = tmp_path.joinpath("dst")

    # simple
    do_copy(movie, lib_path, simple=False)

    parent = lib_path.joinpath("movie", "Title (2022)")
    assert parent.exists()
    assert set(f.name for f in parent.iterdir()) == set(["Title (2022) 2160p AAC.mkv",
                                                                             "Title (2022) 2160p AAC.nfo",
                                                                             "Title (2022) 2160p AAC-poster.jpg",
                                                                             "Title (2022) 2160p AAC-banner.jpg"])
