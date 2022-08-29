import collections
import sys
from types import NoneType
from typing import Callable, Tuple, Any, cast

from lxml import etree as ET
from datetime import datetime

from peets.entities import Movie, MediaFileType, MediaRating


def _uniqueid(root: ET.Element, movie: Movie):
    for k, v in movie.ids.items():
        child = ET.Element("uniqueid",
                           **{"type": k,
                              "default": str(k == "tmdb"),
                              }
                           )
        child.text = str(v)
        root.append(child)

def _country(root, movie: Movie):
    for c in movie.country.split(","):
        child = ET.SubElement(root, "country")
        child.text = c

def _genre(root, movie: Movie):
    for g in movie.genres:
        child = ET.SubElement(root, "genre")
        child.text = g.name # TODO LocalizedName

def _studio(root, movie: Movie):
    for c in movie.production_company.split(","):
        child = ET.SubElement(root, "studio")
        child.text = c

def _credits(ele: str, attr: str) -> Callable[[ET.Element, Movie], None]:
    def _inner(root, movie: Movie):
        for p in movie.__getattribute__(attr):
            child = ET.SubElement(root, "credits")
            child.text = p.name
            if "tmdb" in p.ids:
                child.set("tmdbid", str(p.ids["tmdb"]))
            if "imdb" in p.ids:
                child.set("imdbid", str(p.ids["imdb"]))
            if "tvdb" in p.ids:
                child.set("tvdb", str(p.ids["tvdb"]))
    return _inner

def _actors(ele: str, attr: str) -> Callable[[ET.Element, Movie], None]:

    def _inner(root, movie: Movie):
        for p in movie.__getattribute__(attr):
            actor = ET.SubElement(root, ele)
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

    return _inner

def _showlinks(root, movie: Movie):
    for link in movie.showlinks:
        child = ET.SubElement(root, "showlink")
        child.text = link


NfoTableItem = (str | # direct map
                tuple[str, str] | # key map
                tuple[str, str, Callable[[Any], Any]] | # key remap
                tuple[str, Callable[[Movie], Any]] |  # flexible map
                Callable[[ET.Element, Movie], None]) # most flexible FIXME
NfoTable = list[NfoTableItem]

def _process(item: NfoTableItem, root: ET.Element, movie: Movie):
    """
    FIXME match...case is not suit for this?
    """
    match item:
        case str() as tag:
            child = ET.SubElement(root, tag)
            child.text = str(getattr(movie, tag))
        case (str() as tag, str() as field):
            child = ET.SubElement(root, tag)
            child.text = str(getattr(movie, field))
        case (str() as tag, str() as field,  conv):
            child = ET.SubElement(root, tag)
            child.text = str((cast(Callable, conv))(getattr(movie, field)))
        case (str() as tag, conv):
            child = ET.SubElement(root, tag)
            child.text = str((cast(Callable, conv))(movie))
        case conv:
            (cast(Callable, conv))(root, movie)

def write_nfo(movie: Movie):
    root = ET.Element("movie")
    root.addprevious(ET.Comment(f"created on {datetime.now().isoformat()}"))
    doc = ET.ElementTree(root)

    table: NfoTable = [
        "title",
        ("originaltitle", "original_title"),
        ("sorttitle", "sort_title"),
        ("year", "year",
         lambda year: year if year !=0 else ""),
        ("rating", "ratings",
         lambda ratings: "{:.1f}".format(ratings["tmdb"].rating * 10 / ratings["tmdb"].max_value)), # FIXME tmdb only
        ("userrating", "ratings",
         lambda ratings: ""), # TODO userrating
        ("votes", "ratings",
         lambda ratings: str(ratings["tmdb"].votes)), # FIXME
        ("set", "movie_set",
         lambda movie_set: movie_set.title if movie_set else ""),
        "plot",
        ("outline", "plot"), # FIXME use whole plot
        "tagline",
        "runtime",
        ("thumb", "artwork_url_map",
         lambda artwork_url_map: artwork_url_map.get(MediaFileType.POSTER)),
        ("fanart", "artwork_url_map",
         lambda artwork_url_map: artwork_url_map.get(MediaFileType.FANART)),
        ("mpaa", "certification",
         lambda certification: ""), # TODO CertificationStyle.formatCertification
        ("certification", "certification",
         lambda certification: ""), # TODO same as mapp
        ("id", "ids",
         lambda ids: ids["imdb"]),
        ("tmdbid", "ids",
         lambda ids: ids["tmdb"]),
        # uniqueid
        _uniqueid,
        # country
        _country,
        ("premiered", "release_date"), # TODO reconsider date type
        ("dateadded", "date_added",
         lambda date_added: date_added.strftime("%Y-%m-%d %H:%M:%S")), #TODO MovieGenericXmlConnector#addDateAdded
        ("lockdate",
         lambda movie: "true"), #  protect the NFO from being modified by Emby
        "watched",
        ("playcount",
         lambda movie: 0),  # TODO
        _genre,
        _studio,
        _credits("credits", "writers"),
        _credits("director", "directors"),
        _actors("actor", "actors"),
        _actors("producer", "producers"),
        ("trailer", "trailer",
         lambda trailer: next((t.url for t in trailer if t.in_nfo and t.url.startwith("file")), None)
         ),
        ("source", "media_source"), #TODO
        ("language", "spoken_languages"), #TODO
        _showlinks,
        #KODI
        "top250", #TODO
        #TODO status & code
        #TODO fileinfo
    ]



    for item in table:
        _process(item, root, movie)

    return ET.tostring(doc, pretty_print=True, xml_declaration=True, encoding='UTF-8', standalone=True)
