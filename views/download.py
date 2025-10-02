from types import SimpleNamespace
from typing import Literal

from prompt_toolkit.clipboard.pyperclip import PyperclipClipboard
from yt_dlp.utils import DownloadError
from prompt_toolkit.clipboard.pyperclip import PyperclipClipboard

from track import TrackExtended
from views.search import init as search
from utils import Exit
from utils.views import get_info_term
from utils.config import Config
from utils.prompt import Color, EditableList, List, Confirm, clear

def init(config: Config, url: str, lyrics: str | None = None, genres: list[str] | None = None, comment: list[str] | None = None, track: TrackExtended | None = None):
  url_str = f'[URL: {url}]'
  t: TrackExtended | None = track
  ydl = config.youtube_dl()
  if t is None:
    term = get_info_term(config, url)
    t = search(term, config=config)
    if t is None:
      return False
    
  _comment = comment or [url_str]
  table = t.get_table(genres=genres, comment=_comment)
  before_screen = table

  if not genres:
    valid_genres = t.valid_genres()
    if not valid_genres:
      before_screen += '\n' + Color.get_color('Couldn\'t find genres', Color.ERROR)
  if lyrics is None:
    valid_lyrics = t.valid_lyrics()
    if not valid_lyrics:
      before_screen += '\n' + Color.get_color('Couldn\'t find lyrics', Color.ERROR)

  clear()

  try:
    id = List[Literal['download', 'exit'], None]([
        List.Item("download", "Download") if url else None, 
        List.Item("lyrics", "Lyrics") if url else None,
        List.Item("genres", "Genres") if url else None,
        List.Item("comment", "Comment") if url else None,
        List.Item('exit', 'Exit')
      ], before_screen=before_screen, horizontal=True).get_value()
    download = id == 'download'
    
    if id == 'exit' or id is None:
      return False

    if url and download:
      try:
        file_info = SimpleNamespace(**ydl.extract_info(url, download=download))
        t.set_ext(file_info.audio_ext)
        t.metadata(custom_lyrics=lyrics, custom_genres=genres, comment=_comment)
      except DownloadError as error:
        Confirm(before=f"Couldn't download file: {str(error)}").start()
        return False
      except Exception as error:
        Confirm(before=str(error)).start()
        return False
    if url and id == 'lyrics':
      lyrics = None
      while lyrics is None:
        Confirm(before='Copy lyrics to clipboard').start()
        text = PyperclipClipboard().get_data().text
        lyrics = text if len(text) > 0 else None
      return init(config, url=url, lyrics=lyrics, track=t)
    if url and id == 'genres':
      g = EditableList('Genres', genres or t.genres).init()
      return init(config, url=url, genres=g, track=t)
    if url and id == 'comment':
      _comment = EditableList('Comment', _comment).init()
      return init(config, url=url, track=t, comment=_comment)

    clear()
    Color.print_formatted(table)
    if download:
      Color.print_color('\nDownloaded', Color.SUCCESS)
      t.save()
    Confirm().start(False)
    return True
  except Exit:
    return False
