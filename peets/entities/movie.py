from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID
from peets.entities.media_certification import MediaCertification
from peets.entities.media_entity import MediaEntity
from peets.entities.media_trailer import MediaTrailer
from peets.entities.media_genres import MediaGenres
from peets.entities.person import Person


@dataclass(kw_only=True)
class MovieSet(MediaEntity):
    movie_ids:list[UUID] = field(default_factory=list)
    movies:list["Movie"] = field(default_factory=list)
    title_sortable:str = ""



@dataclass(kw_only=True)
class Movie(MediaEntity):
    sort_title: str = ""
    tagline:str = ""
    runtime:int = 0
    watched:bool = False
    playcount:int = 0
    isDisc:bool = False
    spoken_languages:str = ""
    country:str = ""
    release_date:str = ""
    multi_movie_dir:bool = False
    top250:int = 0
    media_source:str = ""  #TODO see guessit.rules.properties.source
    video_in_3d:bool = False
    certification:MediaCertification = MediaCertification.UNKNOWN
    movie_set_id:UUID | None = None
    edition:str = ""  # TODO see guessit.rules.properties.edition
    stacked:bool = False
    offline:bool = False
    genres:list[MediaGenres] = field(default_factory=list)
    extra_thumbs:list[str] = field(default_factory=list)
    extra_fanarts:list[str] =  field(default_factory=list)
    actors:list[Person]  =  field(default_factory=list)
    producers:list[Person]  =  field(default_factory=list)
    directors:list[Person]  =  field(default_factory=list)
    writers:list[Person]  =  field(default_factory=list)
    trailer:list[MediaTrailer] = field(default_factory=list)
    showlinks:list[str] = field(default_factory=list)
    movie_set: MovieSet | None = None
    title_sortable:str = ""
    original_title_sortable = ""
    other_ids = ""
    late_watched:str = "" # date
    localized_spoken_languages:str = ""
