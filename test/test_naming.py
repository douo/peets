import stat
from os import chmod

from peets.entities import MediaFileType, Movie
from peets.library import Library
from peets.naming import do_copy


def test_do_copy_simple_naming(tmp_path, create_file):
    media_files = [
        (
            MediaFileType.VIDEO,
            "中文名.English.Name.2021.UHD.BluRay.2160p.x265.10bit.HDR.mUHD-FRDS.mkv",
        ),
        (
            MediaFileType.NFO,
            "中文名.English.Name.2021.UHD.BluRay.2160p.x265.10bit.HDR.mUHD-FRDS.nfo",
        ),
        (
            MediaFileType.BANNER,
            "中文名.English.Name.2021.UHD.BluRay.2160p.x265.10bit.HDR.mUHD-FRDS-banner.jpg",
        ),
        (
            MediaFileType.POSTER,
            "中文名.English.Name.2021.UHD.BluRay.2160p.x265.10bit.HDR.mUHD-FRDS-poster.jpg",
        ),
    ]
    media_files = [(t, create_file(n, "src")) for t, n in media_files]
    main_video = media_files[0][1]
    chmod(main_video, 0o754)

    movie = Movie(
        title="Title",
        year=2022,
        audio_codec="AAC",
        screen_size="2160p",
        media_files=media_files,
    )

    lib = Library(tmp_path.joinpath("dst"))

    # simple
    do_copy(movie, lib)

    parent = lib.path.joinpath("movie", "Title (2022)")
    assert parent.exists()
    assert set(f.name for f in parent.iterdir()) == set(
        ["Title (2022) 2160p AAC.mkv", "movie.nfo", "poster.jpg", "banner.jpg"]
    )

    assert stat.S_IMODE(parent.joinpath("movie.nfo").stat().st_mode) == stat.S_IMODE(
        main_video.stat().st_mode
    )


def test_do_copy(tmp_path, create_file):
    media_files = [
        (
            MediaFileType.VIDEO,
            "中文名.English.Name.2021.UHD.BluRay.2160p.x265.10bit.HDR.mUHD-FRDS.mkv",
        ),
        (
            MediaFileType.NFO,
            "中文名.English.Name.2021.UHD.BluRay.2160p.x265.10bit.HDR.mUHD-FRDS.nfo",
        ),
        (
            MediaFileType.BANNER,
            "中文名.English.Name.2021.UHD.BluRay.2160p.x265.10bit.HDR.mUHD-FRDS-banner.jpg",
        ),
        (
            MediaFileType.POSTER,
            "中文名.English.Name.2021.UHD.BluRay.2160p.x265.10bit.HDR.mUHD-FRDS-poster.jpg",
        ),
    ]
    movie = Movie(
        title="Title",
        year=2022,
        audio_codec="AAC",
        screen_size="2160p",
        media_files=[(t, create_file(n, "src")) for t, n in media_files],
    )



    lib = Library(tmp_path.joinpath("dst"))
    lib.config.media_file_naming_style = "full"
    # simple
    do_copy(movie, lib)

    parent = lib.path.joinpath("movie", "Title (2022)")
    assert parent.exists()
    assert set(f.name for f in parent.iterdir()) == set(
        [
            "Title (2022) 2160p AAC.mkv",
            "Title (2022) 2160p AAC.nfo",
            "Title (2022) 2160p AAC-poster.jpg",
            "Title (2022) 2160p AAC-banner.jpg",
        ]
    )
