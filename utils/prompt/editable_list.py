from typing import TypeVar, Generic, Literal, Self

from utils import Exit
from utils.prompt.generic import clear
from utils.prompt.list import List
from utils.prompt.input import default_input

V = TypeVar('V')

class EditableList(Generic[V]):
  def __init__(self, title: str, value: list[V], editable_list: Self | None = None) -> None:
    self.__title = title
    self.__value = editable_list.__value if editable_list else value.copy()
    self.__default_value = editable_list.__default_value if editable_list else self.__value.copy()

    self.__default_index: int = editable_list.__default_index if editable_list else 0
    self.__default_action_index: int = editable_list.__default_action_index if editable_list else 0

  def init(self) -> list[V]:
    clear()
    try:
      (index, _, action, action_index) = List[V, Literal['add-below', 'add-above', 'move-up', 'move-down', 'edit', 'remove', 'save', 'no-save']](
      self.__value,
      self.__title,
      default_index=self.__default_index,
      default_action_index=self.__default_action_index,
      actions=[
        ('add-below', 'Add below', True),
        ('add-above', 'Add above', True),
        ('move-up', 'Move up', len(self.__value) > 0),
        ('move-down', 'Move down', len(self.__value) > 0),
        ('edit', 'Edit', len(self.__value) > 0),
        ('remove', 'Remove', len(self.__value) > 0),
        ('save', 'Save', True),
        ('no-save', 'Exit without saving', True)
      ]).get_action()
    except Exit:
      return  self.__default_value

    if action == 'no-save':
      return self.__default_value
    if action == 'save':
      return self.__value

    self.__default_action_index = action_index
    try:
      if action == 'add-below':
        # Inserts item below current index
        self.__value.insert(index + 1, default_input(self.__title))
        # Sets index for next frame to the same as inserted item
        self.__default_index = min(index + 1, len(self.__value) - 1)
      if action == 'add-above':
        # Inserts item above current index
        self.__value.insert(index, default_input(self.__title))
        # Sets index for next frame to the same as inserted item
        self.__default_index = max(index, 0)
      if action == 'edit':
        # Changes current index value
        self.__value[index] = default_input(self.__title, self.__value[index])
        self.__default_index = index
    except Exit:
      pass
    if action == 'remove':
      # Concat items before current index and after current index
      self.__value = [*self.__value[:index], *self.__value[index + 1:]]
      # Changes default index for next frame to previous
      self.__default_index = max(self.__default_index - 1, 0)
    if action == 'move-up' and index - 1 >= 0:
      # Inverts previous item with current
      self.__value = [*self.__value[:index - 1], self.__value[index], self.__value[index - 1], *self.__value[index + 1:]]
      # Changes default index for next frame to previous
      self.__default_index = max(index - 1, 0)
    if action == 'move-down' and index + 1 < len(self.__value):
      # Inverts next item with current
      self.__value = [*self.__value[:index], self.__value[index + 1], self.__value[index], *self.__value[index + 2:]]
      # Changes default index for next frame to next
      self.__default_index = min(index + 1, len(self.__value) - 1)

        
    return EditableList(self.__title, self.__value, self).init()

