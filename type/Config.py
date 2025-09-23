from enum import Enum
from pathlib import Path
import json
from typing import Literal

from utils.classes import Obj

class UrlModifier(dict):
  title: dict[str, str]
  artist: dict[str, str]
  class Key(Enum):
    TITLE = 'title'
    ARTIST = 'artist'
  class Prop(Enum):
    LYRICS = 'lyrics_url_modifiers'
    GENRES = 'genres_url_modifiers'

class Sort(Enum):
  ARTIST = 'artist'
  TITLE = 'title'
  ALBUM = 'album'
  YEAR = 'year'
class SortType(Enum):
  ASC = 'asc'
  DESC = 'desc'

LyricsProvider = Literal['AzLyrics', 'LyricsOvh', 'Lyrist', 'Genius']

class AppConfig:
  temp_folder: str = str(Path.joinpath(Path.home(), 'tmp'))
  output_folder: str = str(Path.joinpath(Path.home(), "music"))
  artwork_size: int = 1000
  show_count: int = 10
  excluded_genres: list[str] = []
  included_genres: list[str] = {}
  genres_modifiers: dict[str, str] = {}
  lyrics_modifiers: dict[str, str] = {}
  lyrics_url_modifiers: UrlModifier = { "artist": {}, "title": {} }
  genres_url_modifiers: UrlModifier = { "artist": {}, "title": {} }
  lyrics_provider: LyricsProvider = 'AzLyrics'

  class Keys(dict):
    from uuid import UUID
    id: UUID | None = None
    itunes_api_url: str | None = 'https://itunes.apple.com/search'
    temp_folder: str | None = None
    output_folder: str | None = None

  def json(self) -> str:
    obj = {}
    for attr in Obj.get_attributes(self):
      obj[attr] = getattr(self, attr)
    return json.dumps(obj, indent=4)