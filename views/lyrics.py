from prompt_toolkit.clipboard.pyperclip import PyperclipClipboard
from typing import Literal

from utils import Exit
from utils.config import Config
from utils.views import search_menu
from utils.prompt import Confirm, Color, List
from views.search import init as search

def init(config: Config) -> None:

  term = search_menu()
  track = search(term, config=config)

  if track is None:
    Confirm(before=Color.get_color(f"Couldn't find track for {term}", Color.ERROR)).start()
    return

  if not track.valid_lyrics():
    Confirm(before=f"Couldn't find lyrics for {Color.get_color(f'{track.value.artistName} - {track.value.trackName}', Color.PRIMARY)}").start()
    return
  
  lyrics, url = track.get_lyrics(False)

  id = List[Literal['copy', 'exit'], None]([
      List.Item('copy', 'Copy to clipboard'),
      List.Item('exit', 'Exit'),
    ], before_screen=lyrics, horizontal=True, show_count=len(lyrics.split('\n'))).get_value()

  match id:
    case 'copy':
      clipboard = PyperclipClipboard()
      clipboard.set_text(lyrics)

      Confirm(before=Color.get_color('Lyrics coppied to clipboard', Color.SUCCESS)).start()
    case None:
      raise Exit