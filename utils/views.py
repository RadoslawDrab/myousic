import re
from prompt_toolkit.clipboard.pyperclip import PyperclipClipboard


from utils import Exit
from utils.config import Config
from utils.prompt import clear, Input, Color


def search_menu(title: str | None = 'Search', default_artist: str | None = None, default_title: str | None = None):
  try:
    [artist, title] = Input(title, ('Artist: ', default_artist), ('Title: ', default_title)).start()
    return f'{artist} - {title}'
  except Exit:
    return None

def get_artist_track(config: Config, url: str) -> tuple[str, str]:
  ydl = config.youtube_dl()
  info = ydl.extract_info(url, download=False)

  artist: str = info.get('artist') or info.get('creator') or info.get('uploader')
  title: str = info.get('track') or info.get('fulltitle') or info.get('alt_title')

  formatted_title = re.sub(' x ', ', ', re.sub(r'(\\[|\\().*(\\]|\\))', '', title))

  artist_match = re.match(r'.*(?= - )', formatted_title)
  if artist_match and info.get('artist') is not None:
    artist = artist_match.string

  formatted_title = re.sub(r'-', '', re.sub(artist, '', formatted_title, re.I)).strip()

  title_split = formatted_title.split('-')

  return (artist, formatted_title) if re.search(artist.lower(), formatted_title.lower()) is not None or len(title_split) <= 1 else (title_split[0], *title_split[1:])
  
def get_info_term(config: Config, url: str):
  (artist, title) = get_artist_track(config, url)
  return f'{artist} - {title}'
def valid_url(url: str | None):
  return bool(re.match(r'https?://(youtu\.be)|(youtube\.com)/.*', url or ''))
def input_url(config: Config) -> str | None: 
  try:
    clear()
    url = PyperclipClipboard().get_data().text or ''
    title = 'No URL'
    url_valid = valid_url(url)
    if url_valid:
      title = get_info_term(config, url)
      
    
    [url_input] = Input(
      Color.get_color('Youtube info: ', Color.GREY) + Color.get_color(title, Color.PRIMARY), 
      ('YouTube URL' + (f" ({Color.get_color('Enter', Color.SECONDARY)} for default)" if url_valid else '') + ': ', Color.get_color(url, Color.GREY) if url_valid else '')
    ).start()
    
    url = url_input if url_input != '' else url
    if not valid_url(url):
      return input_url(config)

    return url
  except Exit:
    pass
  return None