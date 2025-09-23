from types import SimpleNamespace
from typing import Literal
from yt_dlp.utils import DownloadError

from views.search import init as search
from utils import Exit
from utils.views import get_info_term
from utils.config import Config
from utils.prompt import Color, List, Confirm, clear

def init(config: Config, url: str):
  ydl = config.youtube_dl()
  term = get_info_term(config, url)
  t = search(term, config=config)
  if t is None:
    return False
  
  valid_lyrics = t.valid_lyrics()
  valid_genres = t.valid_genres()
  table = t.get_table()
  before_screen = table

  if not valid_lyrics:
    before_screen += '\n' + Color.get_color('Couldn\'t find lyrics', Color.ERROR)
  if not valid_genres:
    before_screen += '\n' + Color.get_color('Couldn\'t find genres', Color.ERROR)
  
  clear()
  try:
    id = List[Literal['download', 'exit'], None]([
        List.Item("download", "Download") if url else None, 
        List.Item('exit', 'Exit')
      ], before_screen=before_screen, horizontal=True).get_value()
    download = id == 'download'
    
    if id == 'exit' or id is None:
      return False
    
    if url and download:
      try:
        file_info = SimpleNamespace(**ydl.extract_info(url, download=download))
        t.set_ext(file_info.audio_ext)
        t.metadata()
      except DownloadError as error:
        Confirm(before=f"Couldn't download file: {error}").start()
        return False
      except Exception as error:
        Confirm(before=str(error)).start()
        return False
      
    clear()
    Color.print_formatted(table)
    if download:
      Color.print_color('\nDownloaded', Color.SUCCESS)
      t.save()
    Confirm().start(False)
    return True
  except Exit:
    return False
