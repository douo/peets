from peets.entities import (
    MediaAiredStatus,
    MediaCertification,
    MediaFileType,
    MediaGenres,
    Movie,
    TvShow,
    TvShowEpisode,
)
from peets.iso import Country, Language
from peets.tmdb import TmdbArtworkProvider, TmdbMetadataProvider


def test_detail(hijack):
    data = hijack("movie.json")
    tmdb = TmdbMetadataProvider(language=Language.ZH, country=Country.CN)
    m = tmdb.apply(Movie(), id_=0)

    assert m.ids["imdb"] == data["imdb_id"]
    assert int(m.ids["tmdb"]) == data["id"]
    assert m.release_date == "2022-07-08"
    assert m.certification == MediaCertification.US_PG13
    assert m.movie_set.tmdb_id == 131296
    assert m.ids["tmdbSet"] == "131296"
    # print(generate_nfo(m))


def test_artwork(hijack):
    hijack("movie_images.json")

    tmdb = TmdbArtworkProvider(language=Language.ZH, country=Country.CN)

    m = tmdb.apply(Movie(ids={"tmdb": 0}))

    assert m.artwork_url_map == {
        MediaFileType.POSTER: "https://image.tmdb.org/t/p/original/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
        MediaFileType.FANART: "https://image.tmdb.org/t/p/original/5pxdgKVEDWDQBtvqIB2eB2oheml.jpg",
    }


def test_metadata_original_release_date_only(hijack):
    hijack("movie_original_release_date_only.json")

    tmdb = TmdbMetadataProvider(language=Language.ZH, country=Country.CN)
    m = tmdb.apply(Movie(), id_=0)

    assert m.release_date == "2022-07-08"


def test_metadata_certification(hijack):
    hijack("movie_certification.json")
    tmdb = TmdbMetadataProvider(language=Language.ZH, country=Country.CN)
    m = tmdb.apply(Movie(), id_=0)

    assert m.certification == MediaCertification.US_PG13


def test_tvshow(hijack):
    hijack("tvshow.json", "tmdbsimple.TV._GET")
    hijack("season.json", "tmdbsimple.TV_Seasons._GET")
    tmdb = TmdbMetadataProvider(language=Language.ZH, country=Country.CN)
    episodes = [TvShowEpisode(season=1, episode=1)]
    m = tmdb.apply(TvShow(episodes=episodes), id_=0)

    assert m.ids["tmdb"] == "95396"
    assert m.title == "Severance"
    assert m.first_aired == "2022-02-17"
    assert m.country == "US"
    assert m.runtime == 50
    assert m.production_company == "Apple TV+, Red Hour, Endeavor Content, Fifth Season"
    assert m.status == MediaAiredStatus.CONTINUING
    assert m.year == 2022
    assert len(m.actors) == 10
    assert m.ids["imdb"] == "tt11280740"
    assert m.ids["tvdb"] == "371980"
    assert m.certification == MediaCertification.US_TVMA
    assert set(m.genres) == {
        MediaGenres.DRAMA,
        MediaGenres.SCIENCE_FICTION,
        MediaGenres.MYSTERY,
    }
    assert len(m.seasons) == 1
    s = m.seasons[0]
    assert s.air_date == "2022-02-17"
    assert s.episode_count == 9
    assert s.name == "第 1 季"
    assert s.season == 1

    assert len(m.episodes) == 1
    e = m.episodes[0]
    assert e.first_aired == "2022-02-17"
    assert e.ids["tmdb"] == "1982925"
    assert e.season == 1
    assert e.episode == 1
    assert len(e.actors) == 9
