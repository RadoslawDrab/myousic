import requests
import re
import urllib.parse
from bs4 import BeautifulSoup

from utils.text import uppercase

class Lyrics:
  def __init__(self, lyrics_url: str = 'https://lyrist.vercel.app/api'):
    self.lyrics_url = lyrics_url
    self.lyrics_search_url = re.sub('/api', '', self.lyrics_url)
    self.__custom_url: str | None = None
    pass
  def get_url(self, artist: str, title: str):
    return re.sub(r' ', '+', (self.lyrics_url + '/' + (urllib.parse.quote(artist + '/' + title)) if self.__custom_url is None else self.__custom_url).lower())
  def get(self, artist: str, title: str) -> tuple[str | None, str]:
    url = self.get_url(artist, title)
    try:
      response = requests.get(url)
      return self.format(response.json()['lyrics']), url
    except:
      return None, url
  def get_to_file(self, file: str, artist: str, title: str, custom_lyrics: str | None = None) -> tuple[str | None, str]:
    (lyrics, url) = self.get(artist, title) if custom_lyrics is None else (custom_lyrics, '')
    if lyrics is not None:
      with open(file, 'w', encoding='utf-8') as f:
        f.write(lyrics)
      return lyrics, url
    return None, url
  def format(self, lyrics: str) -> str:
    return re.sub(r'^\n*', r'\n', re.sub(r'\n*\[.*\]', r'\n', lyrics), flags=re.NOFLAG)
  

class Genre:
  def __init__(self, page_url: str = 'https://www.last.fm/music/{artist}/_/{title}/+tags', excluded_genres: list[str] = [], included_genres: list[str] = [], modifiers: dict[str, str] = {}):
    self.page_url = page_url
    self.excluded_genres = excluded_genres
    self.included_genres = included_genres
    self.modifiers = modifiers
    self.__parse = True

    pass
  def is_valid(self, genre: str):
    # Searches for specific string which is in 'included_genres' but not in 'excluded_genres'
    if len(self.excluded_genres) > 0 and len(self.included_genres) > 0:
      new_included = list(filter(lambda included: included not in self.excluded_genres , self.included_genres))
      for excluded in self.excluded_genres:
        if re.match(excluded, genre) is not None:
          return False
      for included in new_included:
        if re.search(included, genre) is not None:
          return True
      return False
    elif len(self.excluded_genres) > 0:
      for excluded in self.excluded_genres: 
        if re.search(excluded, genre) is None:
          return True
      return False
    elif len(self.included_genres) > 0:
      for included in self.included_genres:
        if re.search(included, genre) is not None:
          return True
      return False
    else:
      return True
  def parse(self, value: bool):
    self.__parse = value
  def __genres_modifiers(self, text: str):
    new_text = text
    for regex in self.modifiers.keys():
      new_text = re.sub(regex, self.modifiers[regex], new_text)
    return new_text
  def get_url(self, artist: str, title: str) -> str:
    if not artist:
      artist = ''
    if not title:
      title = ''
    _artist = urllib.parse.quote_plus(artist) if self.__parse else re.sub('/$', '', re.sub('^/', '', artist))
    _title = urllib.parse.quote_plus(title) if self.__parse else re.sub('/$', '', re.sub('^/', '', title))
    url = self.page_url.format(artist=_artist, title=_title).lower()

    page = requests.get(url)
    if not page.ok and self.__parse == False:
      self.parse(True)
      return self.get_url(artist, title)
    return re.sub(r' ', '+', url)
    
  def get(self, artist: str, title: str):
    page = requests.get(self.get_url(artist, title))
    soup = BeautifulSoup(page.content, 'html.parser')

    selection = soup.select(f'h3 a[href^="/tag"]')
    genres: list[str] = []
    for s in selection:
      genres.append(self.__genres_modifiers(uppercase(s.text)))
      
    filtered = set(filter(lambda genre: self.is_valid(genre), genres))
    return filtered
  def get_str(self, genres: list[str], prefix: str | None = None, suffix: str | None = None, splitter: str = ' '):
    if len(genres) == 0:
      return '-'

    new_str = ''
    pre = prefix if prefix is not None else ''
    suf = suffix if suffix is not None else ''

    for genre in genres:
      new_str += pre + genre + suf + splitter
    return new_str