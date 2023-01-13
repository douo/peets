import re
from typing import Callable, TypeVar, cast

from lxml import etree as ET

from peets.entities import (
    MediaEntity,
    MediaFileType,
    Person
)
from peets.nfo import NfoTable, _to_text, create_element


def _uniqueid(default) -> Callable[[dict], list[ET._Element]]:
    return lambda ids: [
        create_element("uniqueid", str(v), **{"type": k, "default": str(k == default)})
        for k, v in ids.items()
    ]


_uniqueid_default = _uniqueid("tmdb")


def _country(country) -> list[ET._Element]:
    return [create_element("country", c) for c in country.split(",")]


def _genre(genres) -> list[ET._Element]:
    return [create_element("genre", g.text()) for g in genres]


def _studio(production_company) -> list[ET._Element]:
    return [create_element("studio", c) for c in production_company.split(",")]


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


def _outline(plot) -> str:
    """
    从 plot 中取出最少 20 字符的句子
    """
    outline = ""
    prog = re.compile(r".+?[.?!。？！]")
    pos = 0
    while len(outline) < 20 and (result := prog.match(plot, pos)):
        outline += result.group(0)
        pos += result.end()

    return outline or plot


def _thumb(artwork_url_map: dict[MediaFileType, str]) -> list[ET._Element]:
    def inner(type_: MediaFileType, aspect=None) -> ET._Element | None:
        aspect = aspect or type_.name.lower()
        if url := artwork_url_map.get(type_):
            return create_element("thumb", url, aspect=aspect)
        return None

    result = [
        inner(MediaFileType.POSTER),
        inner(MediaFileType.BANNER),
        inner(MediaFileType.CLEARART),
        inner(MediaFileType.CLEARLOGO),
        inner(MediaFileType.THUMB),
        inner(MediaFileType.KEYART),
        inner(MediaFileType.LOGO),
        inner(MediaFileType.CHARACTERART),
        inner(MediaFileType.DISC, "discart"),
    ]

    return [r for r in result if r is not None]


def _tags(tags) -> list[ET._Element]:
    return [create_element("tag", t) for t in tags]


def _credits(ele: str, attr: str) -> Callable[[MediaEntity], list[ET._Element]]:
    def _inner(entity: MediaEntity) -> list[ET._Element]:
        result = []
        for p in entity.__getattribute__(attr):
            child = ET.Element("credits")
            child.text = p.name
            if "tmdb" in p.ids:
                child.set("tmdbid", str(p.ids["tmdb"]))
            if "imdb" in p.ids:
                child.set("imdbid", str(p.ids["imdb"]))
            if "tvdb" in p.ids:
                child.set("tvdb", str(p.ids["tvdb"]))
            result.append(child)
        return result

    return _inner


def _actors(ele: str, attr: str) -> Callable[[MediaEntity], list[ET._Element]]:
    def _inner(entity: MediaEntity) -> list[ET._Element]:
        result = []
        for p in entity.__getattribute__(attr):
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

    return _inner
