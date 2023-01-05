from pathlib import Path

from pytest import fixture

from peets.entities import MediaEntity, MediaFileType, Movie, TvShow
from peets.guessit import NonMedia, create_entity
from peets.ui import interact


@fixture
def create_media(create_media_with_path):
    def _creator(
        name: list | str, parent: Path | str | None = None
    ) -> list[MediaEntity] | MediaEntity:
        result = create_media_with_path(name, parent)
        if type(result) is list:
            return [m for (m, f) in result]
        else:
            return result[0]

    return _creator


@fixture
def create_media_with_path(create_file):
    def _creator(
        name: list | str, parent: Path | str | None = None
    ) -> list[MediaEntity] | MediaEntity:
        result = create_file(name, parent, True)
        if type(result) is list:
            return [(create_entity(f), f) for f in result]
        else:
            return (create_entity(result), result)

    return _creator


def test_create_entity_with_movie(create_media):
    movie = create_media("English.Name.2020.AAC-HE_LC_8ch.mkv")

    assert isinstance(movie, Movie)
    assert movie.title == "English Name"
    assert movie.year == 2020
    assert movie.original_filename == "English.Name.2020.AAC-HE_LC_8ch.mkv"
    assert not movie.multi_movie_dir

    movie = create_media("中文名.2021.UHD.BluRay.2160p.x265.10bit.HDR.mUHD-FRDS.mkv")
    assert isinstance(movie, Movie)
    assert movie.title == "中文名"
    assert movie.year == 2021
    assert movie.multi_movie_dir

    # 国内常用的命名规则
    movie = create_media(
        "中文名.English.Name.2021.UHD.BluRay.2160p.x265.10bit.HDR.mUHD-FRDS.mkv"
    )
    assert isinstance(movie, Movie)
    assert movie.title == "中文名"
    assert movie.original_title == "English Name"
    assert movie.year == 2021
    assert movie.multi_movie_dir


def test_create_entity_with_movie_mediafile(create_media):
    files = [
        "movie with set graphics.avi",
        "movie with set graphics.nfo",
        "movieset-banner.jpg",
        "movieset-clearart.jpg",
        "movieset-clearlogo.jpg",
        "movieset-fanart.jpg",
        "movieset-logo.jpg",
        "movieset-poster.jpg",
    ]

    excepts = [
        MediaFileType.VIDEO,
        MediaFileType.NFO,
        MediaFileType.BANNER,
        MediaFileType.CLEARART,
        MediaFileType.CLEARLOGO,
        MediaFileType.FANART,
        MediaFileType.LOGO,
        MediaFileType.POSTER,
    ]

    media = create_media(files)

    movie = media[0]

    assert isinstance(movie, Movie)
    assert len(movie.media_files) == len(excepts)
    assert set([f[0] for f in movie.media_files]) == set(excepts)


def test_create_entity_with_trailer(create_media):
    assert NonMedia.TRAILER == create_media("Hight.Town.2020.AAC-HE_LC_8ch.trailer.mkv")
    assert NonMedia.TRAILER == create_media(
        "Hight.Town.2020.AAC-HE_LC_8ch.trailer_sample.mkv"
    )


def test_create_entity_with_sample(create_media):
    assert NonMedia.SAMPLE == create_media("Hight.Town.2020.AAC-HE_LC_8ch.sample.mkv")


def test_create_tvshow(create_file):
    parent = "Severance.S01.2160p.ATVP.WEB-DL.DDP5.1.Atmos.HEVC-TEPES"
    f1, f2 = create_file(
        [
            "Severance.S01E01.Good.News.About.Hell.REPACK.2160p.ATVP.WEB-DL.DDP5.1.Atmos.HEVC-TEPES.mkv",
            "Severance.S01E02.Good.News.About.Hell.REPACK.2160p.ATVP.WEB-DL.DDP5.1.Atmos.HEVC-TEPES.mkv",
        ],
        parent=parent,
    )

    processed = set()
    m1 = create_entity(f1, processed)
    assert isinstance(m1, TvShow)
    assert len(m1.episodes) == 2
    assert all((e.season == 1 for e in m1.episodes))

    # test processed
    assert f1 in processed and f2 in processed
    assert f1.parent in processed

    # f2 与 f1 属于相同 episode
    # f2 已被 m1 处理
    # 所以应该返回 NonMedia.PROCESSED
    # 确保不被重复处理
    m2 = create_entity(f2, processed)
    assert m2 is NonMedia.PROCESSED

    f3 = create_file(
        "Severance.S01E03.Good.News.About.Hell.REPACK.2160p.ATVP.WEB-DL.DDP5.1.Atmos.HEVC-TEPES.mkv",
        parent=parent,
    )
    m3 = create_entity(f3, processed)
    # f3 不在 processed 中
    # 当其父目录在，也不会重复处理
    assert m3 is NonMedia.PROCESSED

    # fixme
    # media file
    mf = [
        f"{f1.stem}.nfo",
        f"{f1.stem}-banner.jpg",
        f"{f1.stem}-clearart.jpg",
        f"{f1.stem}-clearlogo.jpg",
        f"{f1.stem}-fanart.jpg",
        f"{f1.stem}-logo.jpg",
        f"{f1.stem}-poster.jpg",
    ]

    excepts = [
        MediaFileType.NFO,
        MediaFileType.BANNER,
        MediaFileType.CLEARART,
        MediaFileType.CLEARLOGO,
        MediaFileType.FANART,
        MediaFileType.LOGO,
        MediaFileType.POSTER,
    ]
    mf = create_file(mf, parent)

    m = create_entity(f1, set())
    assert isinstance(m, TvShow)
    assert len(m.episodes) == 3
    assert len(m.retrieve_episode(1, 2).media_files) == 1
    assert len(m.retrieve_episode(1, 3).media_files) == 1
    mf_episode = [
        mf[0]
        for mf in m.retrieve_episode(1, 1).media_files
        if mf[0] != MediaFileType.VIDEO
    ]
    assert set(mf_episode) == set(excepts)

    # interact(m, tmp_path, "simple")


def test_create_multiple_episodes_tvshow(create_file):
    f1 = create_file("Firefly - S01E01-02 - Serenity & The Train Job.mkv")
    # media file
    mf = [
        f"{f1.stem}.nfo",
        f"{f1.stem}-banner.jpg",
        f"{f1.stem}-clearart.jpg",
        f"{f1.stem}-clearlogo.jpg",
        f"{f1.stem}-fanart.jpg",
        f"{f1.stem}-logo.jpg",
        f"{f1.stem}-poster.jpg",
    ]

    excepts = [
        MediaFileType.NFO,
        MediaFileType.BANNER,
        MediaFileType.CLEARART,
        MediaFileType.CLEARLOGO,
        MediaFileType.FANART,
        MediaFileType.LOGO,
        MediaFileType.POSTER,
    ]

    mf = create_file(mf)

    m = create_entity(f1)

    assert len(m.episodes) == 2
    e1_mf = [
        mf[0]
        for mf in m.retrieve_episode(1, 1).media_files
        if mf[0] != MediaFileType.VIDEO
    ]
    e2_mf = [
        mf[0]
        for mf in m.retrieve_episode(1, 2).media_files
        if mf[0] != MediaFileType.VIDEO
    ]

    assert set(e1_mf) == set(e2_mf) == set(excepts)
    assert (
        m.retrieve_episode(1, 1).multi_episode
        and m.retrieve_episode(1, 2).multi_episode
    )
