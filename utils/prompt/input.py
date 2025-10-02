from typing import TypeVar
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from tabulate import tabulate

from utils.prompt.color import Color
from utils.prompt.generic import clear
from utils import Exit

class Input:
  def __init__(self, title: str | None = None, *prompts: str | tuple[str, str | None]):
    self.__prompts: list[str | tuple[str, str]] = list(prompts)
    self.__values: list[str] = []
    self.__title = title
    
    self.__ps = PromptSession()
    pass
  def start(self, clear_screen: bool = True, padding_left: int = 2, show_info: bool = True):
    if clear_screen:
      clear()
    if show_info:
      table = tabulate(
        [[Color.get_color('CTRL + C', Color.GREY), Color.get_color('Exit', Color.GREY)]],
        tablefmt='plain'
      )
      Color.print_formatted(table)
    if self.__title:
      Color.print_formatted(self.__title)
    try:
      for prompt in self.__prompts:
        padding = ''.ljust(padding_left)
        text = padding
        placeholder = None
        if type(prompt) == str:
          text += prompt
        elif type(prompt) == tuple:
          text += prompt[0]
          placeholder = prompt[1]

        value = self.__ps.prompt(HTML(text), placeholder=HTML(placeholder) if placeholder else '') or placeholder or ''
        if value is None:
          continue
        
        self.__values.append(Color.remove_color(value))
      if clear_screen:
        clear()
      return self.__values
    except KeyboardInterrupt:
      raise Exit

V = TypeVar("V", int, str)
def default_input(name: str, value: V | None = None) -> V:
  """
  Parameters:
    name (`str`): input name
    value (`V | None`): default value

  Returns:
    `V` - same type as value
  """
  [v] = Input(
    name, 
    (f'{'New' if value else 'Set'}: ', Color.get_color(str(value or ''), Color.GREY))
  ).start()

  return int(v) or value if type(value) is int else v or value