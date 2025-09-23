from typing import Callable, Generic, TypeVar
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout import Layout, BufferControl, Window, HSplit, AnyContainer
from prompt_toolkit.widgets import Label, HorizontalLine, Box
from prompt_toolkit.formatted_text import HTML
from tabulate import tabulate


from utils.prompt.color import Color
from utils.prompt.processors import FormatText
from utils.prompt.xml import xml_format
from utils.classes import Listener
from utils.number import clamp
from utils import Exit
from type.Config import SortType

Id = TypeVar('Id')
ActionId = TypeVar('ActionId', bound=str | None)
class ListItem(Generic[Id]):
  def __init__(self, id: Id, name: str | None = None) -> None:
    self.id = id
    self.name = name
    
class ListSortFunction(Callable[[str, SortType], list[ListItem[Id] | Id | str]]):
  pass
class CustomBindingFunction(Callable[[list[ListItem[Id] | Id | str], int], list[ListItem[Id] | Id | str]]):
  pass
class CustomBinding(tuple[str, str, CustomBindingFunction]):
  pass

class List(Generic[Id, ActionId]):
  Item = ListItem
  def __init__(self, 
      items: list[ListItem[Id] | Id | str | tuple[Id, str] | None], 
      title: str | None = None, 
      loop: bool = True, 
      ordered: bool = True, 
      multiple: bool = False, 
      prefix: str | None = None, 
      selector: str = '>', 
      show_count: int = 10, 
      before_screen: str | None = None,
      horizontal: bool = False, 
      sort_types: list[str] | None = None, 
      sort_listener: ListSortFunction | None = None, 
      show_info: bool = False, selection_color: str = Color.SECONDARY, 
      list_prefix: bool = True, 
      custom_bindings: dict[str, CustomBinding] = {},
      on_custom_binding: Callable[[str, list[ListItem[Id]], int], None] = None,
      actions: list[tuple[ActionId, str, bool]] = [],
      default_action_index: int = 0,
      default_index: int = 0
      ):
    """
    Parameters:
      actions: `list[tuple[ActionId, str, bool]]` - List with tuples where: `[action_id, name, enabled]`
    """
    self.items: list[ListItem[Id]] = self.__set_items(items)
    self.__default_items = self.__set_items(items)
    self.selected = []
    self.__current_index: int = len(self.items) + default_index if default_index < 0 else default_index 

    self.title = title
    self.loop = loop
    self.ordered = ordered
    self.multiple = multiple
    self.prefix = prefix
    self.selector = selector
    self.show_count = show_count
    self.before_screen = before_screen
    self.horizontal = horizontal
    self.sort_types = sort_types
    self.sort_type_index: int = -1
    self.sort_dir: SortType = SortType.ASC
    self.list_prefix = list_prefix
    self.__show_info: bool = show_info
    self.__selection_color = selection_color
    self.custom_bindings = custom_bindings
    self.actions = actions
    self.__current_action_index = default_action_index
    self.__on_custom_binding = on_custom_binding
    self.__set_ended(False)
    
    self.__bindings = KeyBindings()

    self.__sort_listener = Listener[ListSortFunction]() 
    
    if sort_listener:
      self.__sort_listener.set(sort_listener)
    
    self.__buffer = Buffer()
    self.__header = Label(self.title)
    self.__controls = Label('')
    self.__content = Window(content=BufferControl(buffer=self.__buffer, input_processors=[FormatText()]))
    self.__update_root((HSplit([
      Box(self.__controls, padding_left=2, padding=0),
      HorizontalLine(),
      Box(self.__header, padding_left=2, padding=0),
      HorizontalLine(),
      Box(self.__content, padding_left=2, padding=0)
    ])))

    self.__init_bindings()
    self.__set_action(1)
    self.__set_action(-1)
    
  def __init_bindings(self) -> None:
    @self.__bindings.add('enter')
    def _(e): 
      self.__set_ended(True)
      e.app.exit(result=False)
    self.__bindings.add('c-c')(lambda e: e.app.exit(result=True))
    
    self.__bindings.add('left' if self.horizontal else 'up')(lambda e: self.__up())
    self.__bindings.add('right' if self.horizontal else 'down')(lambda e: self.__down())
    if self.multiple:
      self.__bindings.add('space')(lambda e: self.__select_current())
      self.__bindings.add('c-a')(lambda e: self.select_all_toggle())
    
    if self.sort_types is not None and len(self.sort_types) > 0:
      self.__bindings.add('s-up')(lambda e: self.__change_sort())
      self.__bindings.add('s-down')(lambda e: self.__change_sort(-1))
      self.__bindings.add('s-tab')(lambda e: self.__change_sort_dir())
    if len(self.actions) > 1:
      self.__bindings.add('s-left')(lambda e: self.__set_action(-1))
      self.__bindings.add('s-right')(lambda e: self.__set_action())
    self.__bindings.add('tab')(lambda e: self.__toggle_show_info())
    
    if len(self.custom_bindings.keys()) > 0:
      for key in self.custom_bindings:
        self.__bindings.add(*key.split(' '))(lambda event: self.__custom_binding_event(event))
    
  def __custom_binding_event(self, event: KeyPressEvent) -> None:
    event_key = ' '.join([k.key for k in event.key_sequence])
    self.__buffer.insert_text(event_key)
    keys = self.custom_bindings.keys()
    if event_key not in keys:
      return

    binding = self.custom_bindings[event_key]
    
    if self.__on_custom_binding: self.__on_custom_binding(event_key, self.items, self.__current_index)
    (_, _, func) = binding
    self.__set_items(func(self.items, self.__current_index))
    self.__show()

  def __get_custom_bindings_names(self) -> list[tuple[str, str]]:
    """
    Returns:
      `list[tuple[str, str]]` - `list[tuple[key_name, description]]`
    """
    l: list[tuple[str, str]] = []
    for key in self.custom_bindings:
      binding = self.custom_bindings[key]
      (key_name, key_type, _) = binding
      l.append((key_name, key_type))
    return l

  def __update_root(self, container: AnyContainer | Callable[[AnyContainer], AnyContainer]) -> None:
    if isinstance(container, AnyContainer):
      self.__root = container
    else:
      self.__root = container(self.__root)
  def __set_items(self, items: list[ListItem[Id] | Id | str | tuple[Id, str] | None] | None, replace: bool = True) -> list[ListItem[Id]]:
    if items is None:
      return self.__set_items(self.__default_items)

    new_items: list[ListItem[Id]] = [] if replace else self.items

    for index in range(len(items)):
      item = items[index]
      d: ListItem[Id]
      if type(item) is str:
        d = ListItem(item)
      elif type(item) is tuple:
        d = ListItem(*item)
      elif isinstance(item, ListItem):
        d = item
      else:
        d = ListItem(item, str(item))

      new_items.append(d)
    self.items = new_items
    
    return new_items
  
  def __up(self) -> None:
    if self.loop:
      self.__current_index -= 1
      if self.__current_index < 0:
        self.__current_index = len(self.items) - 1
    else:
      self.__current_index = clamp(self.__current_index - 1, 0, len(self.items) - 1)
    self.__show()
  def __down(self) -> None:
    if self.loop:
      self.__current_index += 1
      if self.__current_index >= len(self.items):
        self.__current_index = 0
    else:
      self.__current_index = clamp(self.__current_index + 1, 0, len(self.items) - 1)
    self.__show()
  def __select_current(self) -> None:
    self.__select(self.__current_index)
  def __select(self, index: int) -> None: 
    if index in self.selected:
      self.selected = list(filter(lambda i: i != index, self.selected))
    else:
      self.selected.append(index)
    self.__show()
  def select_all_toggle(self) -> None:
    if len(self.selected) == len(self.items):
      self.selected = []
    else:
      self.selected = [i for i in range(len(self.items))]
    self.__show()
      
  def __toggle_show_info(self) -> None:
    self.__show_info = not self.__show_info
    self.__show()
  def __set_ended(self, value: bool) -> None:
    self.__ended = value
  
  def get_action(self) -> tuple[int, Id, ActionId, int]:
    """
    Returns current action

    Returns:
      `tuple[int, Id, ActionId, int]` - `tuple[current_item_index, current_action_id, current_action_index]`
    """
    index = self.get_index()
    value = self.items[index].id if len(self.items) > 0 and self.items[index] else None
    return index, value, self.actions[self.__current_action_index][0], self.__current_action_index
  def get_index(self) -> int:
    try:
      self.__show()
  
      application = Application(Layout(self.__root), key_bindings=self.__bindings)
      self.app = application
      output = self.app.run()    
      if output: raise Exit

      return self.__current_index
    except KeyboardInterrupt:
      raise Exit
  def get_value(self) -> Id | None:
    index = self.get_index()
    return self.items[index].id
  def __show(self) -> None:
    if self.__ended: 
      return None
    
    self.__get_controls()
    self.__get_info()
    self.__buffer.reset()
    
    text = ''
    show_count_half = round(self.show_count / 2)
    greater_than_show_count = len(self.items) >= self.show_count
    items = list(filter(lambda i: (i >= self.__current_index - show_count_half and i < self.__current_index + show_count_half) or len(self.items) <= self.show_count, range(len(self.items))))
    if len(items) < self.show_count and len(self.items) > self.show_count:
      is_last = items[len(items) - 1] >= len(self.items) - 1
      if is_last: 
        for index in range(self.show_count - len(items)):
          items.append(index)
      else:
        reversed_items = self.items.copy()
        reversed_items.reverse()
        for index in range(len(reversed_items) - 1, len(reversed_items) - self.show_count + len(items) - 1, -1):
          items.insert(0, index)

    longestItemSize = max(
        0, 
        *[len(item.name or item.id) for item in self.items] 
      ) if len(self.items) > 0 else 0
    for index in items:
      item = self.items[index]
      value = item.name or item.id
      prefix = ((f'{index + 1}'.rjust(len(str(len(items)))) + '.' if self.ordered else '-') + ' ' if not self.horizontal else '') if self.list_prefix else ''
      is_selected = index in self.selected
      is_current_index = index == self.__current_index
      term = (f'{self.selector} ' if is_selected else '  ') + prefix + value if self.multiple else prefix + value

      end = '\n' if not self.horizontal or (self.horizontal and index == len(items) - 1) else ' | '
      print_line = index == 0 and index != items[0] and greater_than_show_count and not self.horizontal
      has_items_from_end = index < items[0]
      is_last = index == items[len(items) - 1]
      if print_line:
        text += Color.get_color(''.ljust(longestItemSize + len(prefix), '-'), Color.GREY) + '\n'
      term = xml_format(term)
      if is_current_index:
        text += Color.get_color(term, self.__selection_color)
      else:
        text += term
      text += end
      if not has_items_from_end and is_last:
        text += '\n'
    # self.__buffer.reset()
    self.__buffer.insert_text(text, True)
  
  def __get_controls(self) -> None:
    def get(text: str):
      return Color.get_color(text, Color.GREY)
    data: list[list[str]] = []
    data.append([get('Tab'), get(f'{"Hide" if self.__show_info else "Show"} controls')])
    
    if self.__show_info:
      data.append([get('Left/Right arrows' if self.horizontal else 'Up/Down arrows'), get('Move left/right' if self.horizontal else 'Move up/down')])
      data.append([get('Enter'), get('Confirm')])
      data.append([get('CTRL + C'), get('Exit')])
    
      if self.sort_types != None and len(self.sort_types) > 0:
        data.append([get('Shift + Up/Down arrows'), get('Change type')])
        data.append([get('Shift + Tab'), get('Change direction')])
      
      if self.multiple:
        data.append([get('Space'), get('Select')])
        data.append([get('CTRL + A'), get('Select all')])
        
      if len(self.custom_bindings.keys()) > 0:
        for binding in self.__get_custom_bindings_names():
          data.append([get(binding[0]), get(binding[1])])
      if len(self.actions) > 1:
        data.append([get('Shift + Left/Right arrows'), get('Change action')])
    
    table = tabulate(data, tablefmt='plain')
    self.__controls.formatted_text_control.text = HTML(table)
  def __get_info(self) -> None:
    text = ''
    try:
      if self.before_screen != None:
        text += self.before_screen + '\n'

      if self.title != None:
        if self.prefix != None:
          text += Color.get_color(self.prefix, Color.SECONDARY) + ' '
        text += (self.title)
        
      if self.sort_types != None and len(self.sort_types) > 0:
        text += '\nSort: '
        if self.sort_type_index != -1:
          text += f'{self.sort_types[self.sort_type_index]} ({self.sort_dir.value.upper()})'
        else:
          text += '- '
      if len(self.actions) > 1:
        text += '\nAction: '
        actions: list[str] = []
        for action_index in range(len(self.actions)):
          action = self.actions[action_index]
          if action[2] == False:
            actions.append(Color.get_color(action[1], Color.GREY))
            continue
          if action_index == self.__current_action_index:
            actions.append(Color.get_color(action[1], Color.SECONDARY))
          else:
            actions.append(action[1])
        
        text += ' | '.join(actions)
    
      self.__header.formatted_text_control.text = HTML(xml_format(text))
    except Exception as error:
      self.__header.formatted_text_control.text = Color.get_color(str(error), Color.ERROR) + '\n\n' + text

  def __set_action(self, value: int = 1) -> None:
    if len(self.actions) <= 0 or all([action[2] == False for action in self.actions]):
      return
    self.__current_action_index += value
    if self.__current_action_index >= len(self.actions):
      self.__current_action_index = 0
    if self.__current_action_index < 0:
      self.__current_action_index = len(self.actions) - 1
    if self.actions[self.__current_action_index][2] == False and value != 0:
      return self.__set_action(value)
    self.__show()
  def __change_sort(self, step: int = 1) -> None:
    self.sort_type_index += max(min(step, 1), -1)
    if self.sort_type_index >= len(self.sort_types):
      self.sort_type_index = -1
    if self.sort_type_index < -1:
      self.sort_type_index = len(self.sort_types) - 1
    self.__set_items(self.__sort_listener.emit(self.sort_types[self.sort_type_index], self.sort_dir))
    self.__show()
  def __change_sort_dir(self) -> None:
    if self.sort_type_index != -1:  
      if self.sort_dir == SortType.ASC:
        self.sort_dir = SortType.DESC
      else:
        self.sort_dir = SortType.ASC
      self.__set_items(self.__sort_listener.emit(self.sort_types[self.sort_type_index], self.sort_dir))
      self.__show()
  def set_sort_listener(self, listener: ListSortFunction | None) -> None:
    self.__sort_listener.set(listener)