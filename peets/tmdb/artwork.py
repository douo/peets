from peets.entities import MediaEntity, MediaFileType
from peets.scraper import Feature, Provider
from peets.iso import Country
from peets.merger import replace
from peets.config import Config
import tmdbsimple as tmdb
from .const import PROVIDER_ID, _ARTWORK_BASE_URL


class TmdbArtworkProvider(Provider[MediaEntity]):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self.language = f"{config.language.name}-{config.country.name}".lower()
        self.country = config.country.name
        self.include_adult = config.include_adult
        self.fallback_country = Country.US.name
        self.fallback_lan = "en"

        tmdb.API_KEY = config.tmdb_key  # side effect

    def apply(self, media: MediaEntity, **kwargs) -> MediaEntity:
        m_id = media.ids[PROVIDER_ID]
        api = tmdb.Movies(m_id)
        resp = api.images(
            language=self.language,
            include_image_language=f"{self.fallback_lan},null"
        )
        result: dict[MediaFileType, str] = {}
        sort_key = lambda item: (
            10000 if item["iso_639_1"] == self.language else 0 +
            item["vote_average"] * 1000 +
            item["width"]
        )
        backdrops = sorted(resp["backdrops"], key=sort_key, reverse=True)
        if(any(backdrops)):
            backdrop = backdrops[0]
            result[MediaFileType.FANART] = f"{_ARTWORK_BASE_URL}original{backdrop['file_path']}"

        posters = sorted(resp["posters"], key=sort_key, reverse=True)
        if(any(posters)):
            poster = posters[0]
            result[MediaFileType.POSTER] = f"{_ARTWORK_BASE_URL}original{poster['file_path']}"

        result = media.artwork_url_map | result

        return replace(media, {"artwork_url_map": result})

    @property
    def available_type(self) -> list[str]:
        return ["movie", "episode"]

    @property
    def features(self) -> list[Feature]:
        return [Feature.Artwork]
