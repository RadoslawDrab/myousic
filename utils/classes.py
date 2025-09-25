from typing import Callable, TypeVar, Generic

Function = TypeVar('Function', bound=Callable)
class Listener(Generic[Function]):
  def __init__(self, listener: Function | None = None):
    self.__listener: Function | None = None
    self.set(listener)
    pass
  def set(self, listener: Function | None):
    self.__listener = listener
    return self.__listener
  def emit(self, *args):
    return self.__listener(*args) if self.__listener is not None else None
class Listeners(Generic[Function]):
  def __init__(self, listeners: list[Function] = []):
    self.__listeners = listeners
    pass
  def add(self, listener: Function):
    self.__listeners.append(listener)
    return len(self.__listeners) - 1
  def remove(self, index: int):
    self.__listeners = list(filter(lambda _, i: i != index, self.__listeners))
  def emit(self, *args):
    output: list[tuple[int, list[any]]] = []
    for listener_index in range(len(self.__listeners)):
      listener = self.__listeners[listener_index]
      values = listener(*args)
      output.append((listener_index, [*values]))
    return output
  
class Obj:
  @staticmethod
  def get_attributes(obj: object) -> list[str]:
    return [attr for attr in dir(obj) if not callable(getattr(obj, attr)) and not attr.startswith("__") and not attr.startswith('_')]