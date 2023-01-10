from datetime import datetime
from typing import Callable

from lxml import etree as ET

from peets.entities import MediaFileType, TvShow, TvShowEpisode
from peets.nfo import Connector, NfoTable, _to_text, create_element, inflate


def _uniqueid(ids: dict) -> list[ET._Element]:
    return [
        create_element("uniqueid", str(v), **{"type": k, "default": str(k == "tmdb")})
        for k, v in ids.items()
    ]


def _ratings(ratings) -> ET._Element:
    parent = ET.Element("ratings")

    for id_, rating in ratings.items():
        if id_ == "user":
            continue
        r = ET.SubElement(parent, "rating")
        if id_ == "tmdb":
            r.set("name", "themoviedb")
            r.set("default", "true")
        else:
            r.set("name", id_)
            r.set("default", "false")
        r.set("max", _to_text(rating.max_value))
        ET.SubElement(r, "value").text = "{:.1f}".format(rating.rating)
        ET.SubElement(r, "votes").text = _to_text(rating.votes)

    return parent


def _thumb(type_: MediaFileType, aspect=None) -> Callable:
    aspect = aspect or type_.name.lower()

    def inner(artwork_url_map) -> ET._Element | None:
        if url := artwork_url_map.get(type_):
            return create_element("thumb", url, aspect=aspect)

    return inner


def _season_name(seasons) -> list[ET._Element]:
    return [
        create_element("namedseason", s.name, number=_to_text(s.season))
        for s in seasons
        if s.name
    ]


def _season_artwork(type_: MediaFileType) -> Callable:

    def inner(seasons) -> list[ET._Element]:
        return [
            create_element(
                "thumb",
                s.artwork_url_map[type_],
                aspect=type_.name.lower(),
                type="season",
                season=_to_text(s.season),
            )
            for s in seasons
            if type_ in s.artwork_url_map
        ]
    return inner


def _fanart(artwork_url_map, extra_fanart_urls) -> ET._Element | None:
    urls = []
    if url := artwork_url_map.get(MediaFileType.FANART):
        urls.append(url)
    urls += extra_fanart_urls

    if urls:
        parent = create_element("fanart")
        for url in urls:
            thumb = ET.SubElement(parent)
            thumb.text = url

        return parent


def _episodeguide(key: str) -> ET._Element:
    # FIXME tmdb only
    def inner(ids: dict):
        parent = create_element("episodeguide")
        url = create_element("url", f"http://api.themoviedb.org/3/tv/{_to_text(ids['tmdb'])}?api_key={key}&language={config.name.lower()}")
        parent.append(url)
        return parent

    return inner


def _country(country) -> list[ET._Element]:
    return [create_element("country", c) for c in country.split(",")]


def _genre(genres) -> list[ET._Element]:
    return [create_element("genre", g.text()) for g in genres]


def _studio(production_company) -> list[ET._Element]:
    return [create_element("studio", c) for c in production_company.split(",")]


def _tags(tags) -> list[ET._Element]:
    return [create_element("tag", t) for t in tags]



def _actor(actors: list[Person]) -> list[ET._Element]:
    result = []
    for p in actors:
        actor = ET.Element(ele)
        name = ET.SubElement(actor, "name")

        name.text = p.name

        if p.role:
            child = ET.SubElement(actor, "role")
            child.text = p.role
        if p.thumb_url:
            child = ET.SubElement(actor, "thumb")
            child.text = p.thumb_url
        if p.profile_url:
            child = ET.SubElement(actor, "profile")
            child.text = p.profile_url

        if "tmdb" in p.ids:
            actor.set("tmdbid", str(p.ids["tmdb"]))
        if "imdb" in p.ids:
            actor.set("imdbid", str(p.ids["imdb"]))
        if "tvdb" in p.ids:
            actor.set("tvdb", str(p.ids["tvdb"]))
        result.append(actor)

    return result




class TvShowKodiConnector(Connector[TvShow]):
    def __init__(self, tmdb_key) -> None:
        super().__init__("kodi")
        self.tmdb_key = tmdb_key

    @property
    def available_type(self) -> list[str]:
        return ["tvshow"]

    def generate(self, tvshow: TvShow) -> str:
        root = ET.Element("tvshow")
        root.addprevious(ET.Comment(f"created on {datetime.now().isoformat()}"))
        doc = ET.ElementTree(root)

        table: NfoTable = [
            "title",
            ("originaltitle", "original_title"),
            ("showtitle", "title"),
            ("year", lambda year: year if year != 0 else ""),
            _ratings,
            ("userrating", lambda ratings: ""),  # TODO userrating
            # "outline",
            "plot",
            # "tagline",
            "runtime",
            _thumb(MediaFileType.POSTER),
            _thumb(MediaFileType.BANNER),
            _thumb(MediaFileType.CLEARART),
            _thumb(MediaFileType.CLEARLOGO),
            _thumb(MediaFileType.THUMB),
            _thumb(MediaFileType.KEYART),
            _thumb(MediaFileType.LOGO),
            _thumb(MediaFileType.CHARACTERART),
            _thumb(MediaFileType.DISC, "discart"),
            _season_name,
            _season_artwork(MediaFileType.POSTER),
            _season_artwork(MediaFileType.BANNER),
            _season_artwork(MediaFileType.THUMB),
            _fanart,
            ("mpaa", lambda certification: certification.mpaa()),  # copy
            (
                "certification",  #  copy
                lambda certification: certification.certification,
            ),
            _episodeguide(self.tmdb_key),
            ("tmdbid", lambda ids: ids["tmdb"]), # copy
            _uniqueid, # TODO copy from movie
            ("premiered", "release_date"),  # copy TODO reconsider date type
            (
                "dateadded",  # copy TODO consider DateField
                lambda date_added: date_added.strftime("%Y-%m-%d %H:%M:%S"),
            ),
            ( # copy
                "lockdate",
                lambda: "true",
            ),  # protect the NFO from being modified by Emby
            ("status", lambda status: status.name_),
            # "watched",
            ("playcount", lambda: 0),  # copy
            _genre,  # copy
            _studio,  # copy
            _country,  # copy
            _tags,
            _actor,
            # _trailer, TODO
            ("user_note", "note")
        ]
