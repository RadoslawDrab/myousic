from enum import Enum
from types import SimpleNamespace
from datetime import datetime
import re
from pathlib import Path
import urllib.request, urllib.parse
from typing import Literal

import music_tag
from shutil import move, rmtree

from track.lyrics import AzLyrics, LyricsOvh, Lyrist, Genius, map_provider
from utils import sanitize_filename
from utils.prompt import Input, Color, Confirm, clear
from utils.config import Config
from type.Config import UrlModifier, LyricsProvider
from track.track_data import Genre, Lyrics

class Explicitness(Enum):
  notExplicit = 'notExplicit'
  explicit = 'Explicit'
class Track(dict):
  wrapperType: str = None
  kind: str
  artistId: int = None
  collectionId: int = None
  trackId: int = None
  artistName: str = None
  collectionName: str = None
  trackName: str = None
  collectionCensoredName: str = None
  trackCensoredName: str = None
  artistViewUrl: str = None
  collectionViewUrl: str = None
  trackViewUrl: str = None
  previewUrl: str = None
  artworkUrl30: str = None
  artworkUrl60: str = None
  artworkUrl100: str = None
  collectionPrice: float = None
  trackPrice: float = None
  releaseDate: str = None
  collectionExplicitness: Explicitness = None 
  trackExplicitness: Explicitness = None
  discCount: int = None
  discNumber: int = None
  trackCount: int = None
  trackNumber: int = None
  trackTimeMillis: int = None
  country: str = None
  currency: str = None
  primaryGenreName: str = None
  isStreamable: bool = None

default_track: Track = {
  'wrapperType': None,
  'kind': None,
  'artistId': None,
  'collectionId': None,
  'trackId': None,
  'artistName': None,
  'collectionName': None,
  'trackName': None,
  'collectionCensoredName': None,
  'trackCensoredName': None,
  'artistViewUrl': None,
  'collectionViewUrl': None,
  'trackViewUrl': None,
  'previewUrl': None,
  'artworkUrl30': None,
  'artworkUrl60': None,
  'artworkUrl100': None,
  'collectionPrice': None,
  'trackPrice': None,
  'releaseDate': None,
  'collectionExplicitness': None, 
  'trackExplicitness': None,
  'discCount': None,
  'discNumber': None,
  'trackCount': None,
  'trackNumber': None,
  'trackTimeMillis': None,
  'country': None,
  'currency': None,
  'primaryGenreName': None,
  'isStreamable': None,
}

class TrackExtended:
  def __init__(self, track: dict, audio_file_id: str, config: Config | None = None, lyrics_providers: list[LyricsProvider] | LyricsProvider = ['AzLyrics', 'Genius'], default_lyrics_provider: Lyrics = AzLyrics):
    default: Track = default_track.copy()
    default.update(**track)
    self._default_lyrics_provider = default_lyrics_provider
    self._lyrics_providers = lyrics_providers if type(lyrics_providers) == list else [lyrics_providers]
    self.value_dict: dict = default
    self.update_track(default)

    self.temp_folder = Path(config.data.temp_folder) or Path.joinpath(config.path, Path('tmp'))
    self.output_folder = config.data.output_folder or './'
    self.default_artwork_size = max(config.data.artwork_size, 100)
    self.audio_file_id = audio_file_id
    self.config = config
    self.audio_ext = None
    self._lyrics: list[Lyrics] = []
    self.__is_saved = False
    for provider in self._lyrics_providers:
      self._lyrics.append(map_provider(provider, self._default_lyrics_provider))

    self.Genre = Genre(
      excluded_genres=[f'^{self.value.primaryGenreName}$', *self.config.data.excluded_genres], 
      included_genres=self.config.data.included_genres,
      modifiers=self.config.data.genres_modifiers
    )

    self.find_lyrics_provider()

  def __repr__(self) -> str:
    return f'TrackExtended(id={self.audio_file_id}, title={self.value.trackName}, artist={self.value.artistName}, album={self.value.collectionName}, year={self.get_date()})'
  @property
  def Lyrics(self):
    return self._lyrics[0] if len(self._lyrics) > 0 else self._default_lyrics_provider
  def find_lyrics_provider(self):
    i = 0
    while not self.valid_lyrics() and len(self._lyrics) > 1 and i <= len(self._lyrics_providers):
      self._lyrics.pop(0)
      i += 1
  def get_table(self, print_table: bool = False):
    from tabulate import SEPARATING_LINE, tabulate
    track = self.value
    data = [
      ['Track', Color.get_color(track.trackName, Color.PRIMARY)],
      ['Artist', Color.get_color(track.artistName, Color.PRIMARY)],
      ['Album', track.collectionName if track.collectionName else '-'],
      SEPARATING_LINE,
      ['Genre', track.primaryGenreName if track.primaryGenreName else '-'],
      ['Other Genres', self.get_genres_str()],
      ['Explicitness', track.trackExplicitness if track.trackExplicitness else '-'],
      SEPARATING_LINE,
      ['Date', str(self.get_date())],
      ['Track', f'{track.trackNumber} / {track.trackCount}' if track.trackNumber != None and track.trackCount != None else '-'],
      ['Disc', f'{track.discNumber} / {track.discCount}' if track.discNumber != None and track.discCount != None else '-'],
      SEPARATING_LINE,
      ['Artwork', Color.get_color(self.get_artwork_url(), Color.SECONDARY) if self.get_artwork_url() else '-'],
      ['Lyrics', Color.get_color(self.get_lyrics_url(), Color.SECONDARY)],
      ['Genres', Color.get_color(self.get_genres_url(), Color.SECONDARY)]
    ]

    table = tabulate(data, tablefmt='plain') + '\n'
    if print_table:
      clear()
      Color.print_formatted(table)
      Confirm().start(False)
    return table

  def get_missing(self, included: dict[str, str | tuple[str, str]] = {}, excluded_keys: list[str] = []):
    keys: dict[str, tuple[str, str | None]] = {}
    for key in self.value_dict.keys():
      if len(excluded_keys) > 0 and key in excluded_keys:
        continue
      if len(included.keys()) > 0 and key not in included.keys():
        continue

      if self.value_dict[key] != None:
        continue
      
      new_dict: dict[tuple[str, str | None]] = {}
      k = included.get(key) if len(included.keys()) > 0 else key
      if type(k) is str:
        new_dict[key] = (k + ': ', None)
      if type(k) is tuple:
        new_dict[key] = (k[0] + ': ', k[1])
      
      keys.update(new_dict)
    values = Input('Values', *keys.values()).start()
    for key_index in range(len(keys.keys())):
      key = [*keys.keys()][key_index]
      self.update_track({
        key: values[key_index]
      })
    clear()
      
  def update_track(self, track: dict):
    if not self.value_dict:
      self.value_dict = default_track.copy()
    self.value_dict.update(**track)
    self.value: Track = SimpleNamespace(**self.value_dict)
  def assign_file(self, audio_ext: str):
    self.set_ext(audio_ext)
    file = Path(self.get_file())
    move(file, Path.joinpath(self.get_dir(), file))
    
  def set_ext(self, ext: str):
    self.audio_ext = ext

  def get_dir(self, is_temporary: bool = True):
    user_regex = r'^\~\/'
    is_home = re.match(user_regex, self.output_folder) != None
    dir = Path.joinpath(Path.cwd(), self.temp_folder) if is_temporary else Path.joinpath(Path.home() if is_home else Path.cwd(), re.sub(user_regex, '', self.output_folder))
    Path.mkdir(dir, exist_ok=True)
    return dir
  def get_filename(self, is_temporary: bool = True):
    return sanitize_filename(str(self.audio_file_id if is_temporary else (self.value.artistName + ' - ' + self.value.trackName)))
  def get_file(self, is_temporary: bool = True):
    if self.audio_ext == None:
      raise ValueError('No extension provided')
    return f'{self.get_filename(is_temporary)}.{self.audio_ext}'

  def get_child_file(self, ext: str):
    return Path.joinpath(self.get_dir(), Path(f'{self.get_filename()}.{ext}'))
  def get_temp_audio_path(self):
    return Path.joinpath(self.get_dir(True), Path(self.get_file(True)))
  def get_output_audio_path(self):
    return Path.joinpath(self.get_dir(False), Path(self.get_file(False)))

  def save(self):
    move(self.get_temp_audio_path(), self.get_output_audio_path())
    rmtree(self.temp_folder, ignore_errors=True)

    self.__is_saved = True

  def get_date(self):
    date = self.value.releaseDate
    if date == None:
      return datetime.now().year
    date_regex = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z'
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").year if re.match(date_regex, date) else date if date != '' else datetime.now().year
  def get_artwork_url(self, size: int = 1000):
    return re.sub(r'100x100(?=bb\..{2,4})', f'{max(size, 100)}x{max(size, 100)}', self.value.artworkUrl100) if self.value.artworkUrl100 else None
  def get_lyrics_url(self):
    return self.Lyrics.get_url(self.config.modify_lyrics(UrlModifier.Key.ARTIST, self.value.artistName), self.config.modify_lyrics(UrlModifier.Key.TITLE, self.value.trackName))
  def get_artwork_ext(self):
    return re.match('\\..+$', self.value.artworkUrl100) if self.value.artworkUrl100 else None
  def get_lyrics(self, to_file: bool = True) -> tuple[str | None, str]:
    """
    Retrieves the lyrics of a song and the URL from which they were fetched.

    This function attempts to retrieve the lyrics of a song from an online source.
    It returns a tuple containing two values:
    - The first value is a string representing the lyrics of the song, or `None` if the lyrics could not be found.
    - The second value is the URL from which the lyrics were retrieved.

    Parameters:
      to_file (bool): Choose whether to save lyrics to temp file. Default: True
    Returns:
        tuple: A tuple containing two elements:
            - str | None: The lyrics of the song or None if lyrics are not available.
            - str: The URL from which the lyrics were retrieved.

    Example:
    ```
        lyrics, url = get_lyrics()
        if lyrics:
            print(f"Lyrics: {lyrics}")
        else:
            print("Lyrics not found.")
    ```
    """
    lyrics_file_path = self.get_child_file('txt')
    artist = self.config.modify_lyrics(UrlModifier.Key.ARTIST, self.value.artistName)
    title = self.config.modify_lyrics(UrlModifier.Key.TITLE, self.value.trackName)
    (lyrics, url) = self.Lyrics.get_to_file(str(lyrics_file_path), artist, title) if to_file else self.Lyrics.get(artist, title)
    if lyrics is not None:
      l = lyrics
      modifier = self.config.data.lyrics_modifiers
      for key in [*modifier.keys()]:
        l = re.sub(key, modifier[key], l)
      lyrics = l
    return (lyrics, url)
  def valid_lyrics(self):
    import requests
    return requests.get(self.get_lyrics_url()).ok
  def valid_genres(self):
    import requests
    return requests.get(self.get_genres_url()).ok

  def get_genres_url(self):
    self.Genre.parse(False)
    return self.Genre.get_url(self.config.modify_genres(UrlModifier.Key.ARTIST, self.value.artistName), self.config.modify_genres(UrlModifier.Key.TITLE, self.value.trackName))
  def get_genres_str(self):
    self.Genre.parse(False)
    return self.Genre.get_str(self.config.modify_genres(UrlModifier.Key.ARTIST, self.value.artistName), self.config.modify_genres(UrlModifier.Key.TITLE, self.value.trackName), prefix='[', suffix=']')
  
  def metadata(self, get_lyrics: bool = True, get_genres: bool = True):
    if self.__is_saved:
      raise RuntimeError('Can\'t edit metadata after save')
    # Image file name
    artwork_image_filename = self.get_child_file(self.get_artwork_ext() or 'jpg')

    artwork_url = self.get_artwork_url(self.default_artwork_size)

    if artwork_url:
      # Saves artwork in temp file
      with urllib.request.urlopen(artwork_url) as url:
        with open(artwork_image_filename, 'wb') as f:
          f.write(url.read())
    
    date = str(self.get_date())

    audio = music_tag.load_file(self.get_temp_audio_path())
    audio['title'] = self.value.trackName
    audio['artist'] = self.value.artistName
    audio['composer'] = self.value.artistName
    audio['album-artist'] = self.value.artistName
    audio['album'] = self.value.collectionName
    audio['genre'] = self.value.primaryGenreName
    audio['track-number'] = self.value.trackNumber or 1
    audio['total-tracks'] = self.value.trackCount or 1
    audio['disc-number'] = self.value.discNumber or 1
    audio['total-discs'] = self.value.discCount or 1
    audio['year'] = date 
    if artwork_url:
      with open(artwork_image_filename, 'rb') as file:
        audio['artwork'] = file.read()

    audio.save()

    (lyrics, url) = self.get_lyrics() if get_lyrics else None
    genres = self.get_genres_str() if get_genres else None

    if genres != None:
      audio['comment'] = genres
    if lyrics != None:
      audio['lyrics'] = lyrics

    audio.save()  