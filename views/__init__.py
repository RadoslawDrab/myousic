from pathlib import Path
from typing import Literal
from uuid import uuid4

from views.search import init as search
from views.download import init as download
from views.bare_download import init as bare_download
from views.settings import init as settings
from views.lyrics import init as lyrics

from utils.config import Config
from utils.args import Args
from utils.views import search_menu, input_url
from utils.prompt import clear, List, Color
from utils import Exit

def init():
  clear()
  args = Args()
  config = Config(Path(args.config_path))
  config.set_key('id', uuid4())
  config.set_key('temp_folder', config.data.temp_folder)
  config.set_key('output_folder', config.data.output_folder)

  Path(config.data.temp_folder).mkdir(exist_ok=True)
  Path(config.data.output_folder).mkdir(exist_ok=True)

  try:
    id = List[Literal['search-download', 'search', 'download', 'lyrics', 'settings', 'exit'], None]([
      List.Item("search-download", "Search and Download"), 
      List.Item("search", "Search"), 
      List.Item("download", "Download"), 
      List.Item("lyrics", "Lyrics"), 
      List.Item("settings", "Settings"), 
      List.Item("exit", "Exit")
    ], 
    ordered=False, title=Color.get_color('Myousic', Color.PRIMARY)).get_value()
    
    url: str | None = None
    
    if id == 'search-download' or id == 'download':
      url = input_url(config)
    
    if id == 'search':
      term = search_menu()
      track = search(term, config=config)
      if track is not None:
        track.get_table(True)
    if id == 'search-download' and url:
      download(config, url)
    if id == 'download' and url:
      bare_download(config, url)
    if id == 'lyrics':
      lyrics(config)
    if id == 'settings':
      settings(config)
    if id == 'exit' or id is None:
      return
    init()
  except Exit:
    return
  
