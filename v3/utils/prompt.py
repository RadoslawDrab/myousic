from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout import Layout, BufferControl, Window, HSplit, AnyContainer
from prompt_toolkit.layout.processors import Processor, Transformation, TransformationInput
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.formatted_text import HTML, to_formatted_text, fragment_list_to_text
from prompt_toolkit.widgets import Label, HorizontalLine, Box
from tabulate import tabulate
from typing import Callable
import re
import re

from utils import Exit
from utils.config import SortType
from utils.classes import Listener
from utils.number import clamp
from utils.system import clear 


class Input:
  def __init__(self, title: str | None = None, *prompts: list[str | tuple[str, str]]):
    self.__prompts: list[str | tuple[str, str]] = prompts
    self.__values: list[str] = []
    self.__title = title
    
    self.__ps = PromptSession()
    pass
  def start(self, clear_screen: bool = True, padding_left: int = 2, show_info: bool = True):
    if clear_screen:
      clear()
    if show_info:
      table = tabulate(
        [[get_color('CTRL + C', ColorType.GREY), get_color('Exit', ColorType.GREY)]],
        tablefmt='plain'
      )
      print_formatted(table)
    if self.__title:
      print_formatted(self.__title)
    try:
      for prompt in self.__prompts:
        padding = ''.ljust(padding_left)
        value = padding
        placeholder = None
        if type(prompt) == str:
          value += prompt
        elif type(prompt) == tuple:
          value += prompt[0]
          placeholder = prompt[1]
          
        value = self.__ps.prompt(HTML(value), placeholder=HTML(placeholder) if placeholder else '') or placeholder or ''
        if value == None:
          continue
        
        self.__values.append(remove_color(value))
      return self.__values
    except KeyboardInterrupt:
      raise Exit

class ListItem(dict):
  id: str
  name: str | None = None
class ColorType():
  PRIMARY = '#ff5500'
  SECONDARY = '#0055ff'
  GREY = '#555555'
  ERROR = '#ff0000'
  WARNING = '#ffff00'
  SUCCESS = '#00ff00'

xml_replacements: dict[str, str] = {
  "&": "&amp;"
}
def xml_format(text: str):
  new_text = text
  for key in xml_replacements.keys():
    new_text = re.sub(key, xml_replacements[key], new_text)
  return new_text

class ListSortFunction(Callable[[str, SortType], list[ListItem | str]]):
  pass
class CustomBindingFunction(Callable[[list[ListItem | str], int], list[ListItem | str]]):
  pass
class CustomBinding(tuple[str, str, CustomBindingFunction]):
  pass

class List:
  def __init__(self, 
      items: list[ListItem | str | None], 
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
      show_info: bool = False, selection_color: str = ColorType.SECONDARY, 
      list_prefix: bool = True, 
      custom_bindings: dict[str, CustomBinding] = {},
      on_custom_binding: Callable[[str, list[ListItem], int], None] = None,
      actions: list[tuple[str, str, bool]] = [],
      default_action_index: int = 0,
      default_index: int = 0
      ):
    self.items: list[ListItem] = self.__set_items(items)
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
    self.__set_action(0)
    
  def __init_bindings(self):
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
    
    if self.sort_types != None and len(self.sort_types) > 0:
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
    
  def __custom_binding_event(self, event: KeyPressEvent):
    self.__buffer.insert_text(event_key)
    keys = self.custom_bindings.keys()
    event_key = ' '.join([k.key for k in event.key_sequence])
    if event_key not in keys:
      return

    binding = self.custom_bindings[event_key]
    
    if self.__on_custom_binding: self.__on_custom_binding(event_key, self.items, self.__current_index)
    (name, desc, func) = binding
    self.__set_items(func(self.items, self.__current_index))
    self.__show()

  def __get_custom_bindings_names(self):
    l: list[tuple[str, str]] = []
    for key in self.custom_bindings:
      binding = self.custom_bindings[key]
      (key_name, key_type, func) = binding
      l.append((key_name, key_type))
    return l

  def __update_root(self, container: AnyContainer | Callable[[AnyContainer], AnyContainer]):
    if isinstance(container, AnyContainer):
      self.__root = container
    else:
      self.__root = container(self.__root)
  def __set_items(self, items: list[ListItem | str | None] | None, replace: bool = True) -> list[ListItem]:
    if items == None:
      return self.__set_items(self.__default_items)

    new_items: list[ListItem] = [] if replace else self.items

    for index in range(len(items)):
      item = items[index]
      d = {  }
      if type(item) is str:
        d['id'] = item
      elif type(item) is dict:
        d = { **item }
      if d.get('id') != None:
        new_items.append(d)
    self.items = new_items
    
    return new_items
  
  def __up(self):
    if self.loop:
      self.__current_index -= 1
      if self.__current_index < 0:
        self.__current_index = len(self.items) - 1
    else:
      self.__current_index = clamp(self.__current_index - 1, 0, len(self.items) - 1)
    self.__show()
  def __down(self):
    if self.loop:
      self.__current_index += 1
      if self.__current_index >= len(self.items):
        self.__current_index = 0
    else:
      self.__current_index = clamp(self.__current_index + 1, 0, len(self.items) - 1)
    self.__show()
  def __select_current(self):
    self.__select(self.__current_index)
  def __select(self, index: int): 
    if index in self.selected:
      self.selected = list(filter(lambda i: i != index, self.selected))
    else:
      self.selected.append(index)
    self.__show()
  def select_all_toggle(self):
    if len(self.selected) == len(self.items):
      self.selected = []
    else:
      self.selected = [i for i in range(len(self.items))]
    self.__show()
      
  def __toggle_show_info(self):
    self.__show_info = not self.__show_info
    self.__show()
  def __set_ended(self, value: bool):
    self.__ended = value
  
  def get_action(self):
    index = self.get_index()
    return (index, self.actions[self.__current_action_index][0], self.__current_action_index)
  def get_index(self):
    try:
      self.__show()
  
      application = Application(Layout(self.__root), key_bindings=self.__bindings)
      self.app = application
      output = self.app.run()    
      if output: raise Exit

      return self.__current_index
    except KeyboardInterrupt:
      raise Exit
  def get_value(self):
    index = self.get_index()
    return self.items[index].get('id')
  def __show(self):
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
        *[len(item.get('name') or item.get('id')) for item in self.items] 
      ) if len(self.items) > 0 else 0
    for index in items:
      item = self.items[index]
      value = item.get('name') or item.get('id')
      prefix = ((f'{index + 1}'.rjust(len(str(len(items)))) + '.' if self.ordered else '-') + ' ' if not self.horizontal else '') if self.list_prefix else ''
      is_selected = index in self.selected
      is_current_index = index == self.__current_index
      term = (f'{self.selector} ' if is_selected else '  ') + prefix + value if self.multiple else prefix + value

      end = '\n' if not self.horizontal or (self.horizontal and index == len(items) - 1) else ' | '
      print_line = index == 0 and index != items[0] and greater_than_show_count and not self.horizontal
      has_items_from_end = index < items[0]
      is_last = index == items[len(items) - 1]
      if print_line:
        text += get_color(''.ljust(longestItemSize + len(prefix), '-'), ColorType.GREY) + '\n'
      term = xml_format(term)
      if is_current_index:
        text += get_color(term, self.__selection_color)
      else:
        text += term
      text += end
      if not has_items_from_end and is_last:
        text += '\n'
    # self.__buffer.reset()
    self.__buffer.insert_text(text, True)
  
  def __get_controls(self):
    def get(text: str):
      return get_color(text, ColorType.GREY)
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
  def __get_info(self):
    text = ''
    try:
      if self.before_screen != None:
        text += self.before_screen + '\n'

      if self.title != None:
        if self.prefix != None:
          text += get_color(self.prefix, ColorType.SECONDARY) + ' '
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
            actions.append(get_color(action[1], ColorType.GREY))
            continue
          if action_index == self.__current_action_index:
            actions.append(get_color(action[1], ColorType.SECONDARY))
          else:
            actions.append(action[1])
        
        text += ' | '.join(actions)
    
      self.__header.formatted_text_control.text = HTML(xml_format(text))
    except Exception as error:
      self.__header.formatted_text_control.text = get_color(str(error), ColorType.ERROR) + '\n\n' + text

  def __set_action(self, value: int = 1):
    if len(self.actions) <= 0:
      return
    self.__current_action_index += value
    if self.__current_action_index >= len(self.actions):
      self.__current_action_index = 0
    if self.__current_action_index < 0:
      self.__current_action_index = len(self.actions) - 1
    if self.actions[self.__current_action_index][2] == False:
      return self.__set_action()
    self.__show()
  def __change_sort(self, step: int = 1):
    self.sort_type_index += max(min(step, 1), -1)
    if self.sort_type_index >= len(self.sort_types):
      self.sort_type_index = -1
    if self.sort_type_index < -1:
      self.sort_type_index = len(self.sort_types) - 1
    self.__set_items(self.__sort_listener.emit(self.sort_types[self.sort_type_index], self.sort_dir))
    self.__show()
  def __change_sort_dir(self):
    if self.sort_type_index != -1:  
      if self.sort_dir == SortType.ASC:
        self.sort_dir = SortType.DESC
      else:
        self.sort_dir = SortType.ASC
      self.__set_items(self.__sort_listener.emit(self.sort_types[self.sort_type_index], self.sort_dir))
      self.__show()
  def set_sort_listener(self, listener: ListSortFunction | None):
    self.__sort_listener.set(listener)

def remove_color(text: str):
  match = re.search(r'(?<=\>).*(?=<\/style>)', text)
  inside_styles = re.sub(r'<\/.*>', '', match.group()) if match else None
  return inside_styles if inside_styles else text
def get_color(text: str, type: ColorType | str, modify_type: str = 'fg'):
  return f'<style {modify_type}="{type}">{text}</style>'
def print_formatted(text: str, sep: str = ' ', end: str = '\n', padding_left: int = 2):
  splitted_text = [''.ljust(padding_left) + line for line in text.split('\n')]
  try:
    print_formatted_text(HTML(xml_format('\n'.join(splitted_text))), sep=sep, end=end)
  except:
    print('\n'.join(splitted_text), sep=sep, end=end)
def print_color(text: str, type: ColorType, modify_type: str = 'fg', sep: str = ' ', end: str = '\n'):
  print_formatted(get_color(text, type, modify_type), sep=sep, end=end)

class FormatText(Processor):
    def apply_transformation(self, ti: TransformationInput):
        try:
          fragments = to_formatted_text(HTML(fragment_list_to_text(ti.fragments)))
          return Transformation(fragments)
        except Exception as error:
          return Transformation(ti.fragments)

class Confirm:
  def __init__(self, title: str = f'Press {get_color("Enter", ColorType.SECONDARY)} to continue.'):
    self.__title = title
    
    self.__ps = PromptSession()
    
  def start(self, clear_screen: bool = True, padding_left: int = 2):
    if clear_screen:
      clear()
    try:
        self.__ps.prompt(HTML(''.ljust(padding_left) + self.__title))
    except KeyboardInterrupt:
      raise Exit 
    
class EditableList(List):
  def __init__(self, add_function: CustomBindingFunction | None = None, remove_function: CustomBindingFunction | None = None, edit_function: CustomBindingFunction | None = None, **kwargs):
    bindings: dict[str, CustomBinding] = {}
    if add_function:
      bindings.update({ 'c-n': ('CTRL + N', 'Add', add_function) })
    if remove_function:
      bindings.update({ 'c-d': ('CTRL + D', 'Remove', remove_function) })
    if edit_function:
      bindings.update({ 'c-e': ('CTRL + E', 'Edit', edit_function) })
      
    super().__init__(**kwargs, custom_bindings=bindings)
    pass
  def get_list(self):
    self.get_index()
    return self.items