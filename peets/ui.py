from dataclasses import dataclass
from teletype.components import ChoiceHelper, SelectOne, SelectApproval
from teletype.io import get_key, style_format, style_print, strip_format

from peets.entities import MediaEntity
from peets.tmdb import search, fill



@dataclass
class MediaVO:
    name: str
    year: str
    id_: str


def interact(media: MediaEntity):
    brief(media)
    style_print("search (s), skip (j)", style=["green", "bold"])
    while sel := get_key() :
        match sel:
            case "s":
                item = do_search(media)
                if item:
                    media = fill(media, item["id"])
                    brief(media)
                    return
                else:
                    style_print("Not Found!")
            case "j":
                return
            case "ctrl-c" | "ctrl-z" | "escape":
                return
            case _:
                style_print("search (s), skip (j)", style=["green", "bold"])

def brief(media: MediaEntity):
    print(f"Name: {media.title}")
    print(f"Year: {media.year}")
    for mf in media.media_files:
        print(f"{mf[0].name}: {mf[1]}")


def do_search(media: MediaEntity):
    result = search(media)
    if result:
        choices = [ChoiceHelper(
            s,
            label= f"{s['title']} - {s['release_date']} - {s['popularity']}({s['id']})",
            style="bold"
        ) for s in result]
        return SelectOne(choices).prompt()
