import re
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML
from utils.prompt.xml import xml_format

class ColorType:
  PRIMARY = '#ff5500'
  SECONDARY = '#0055ff'
  GREY = '#555555'
  ERROR = '#ff0000'
  WARNING = '#ffff00'
  SUCCESS = '#00ff00'


class Color(ColorType):
  @staticmethod
  def remove_color(text: str):
    match = re.search(r'(?<=>).*(?=</style>)', text)
    inside_styles = re.sub(r'</.*>', '', match.group()) if match else None
    return inside_styles if inside_styles else text

  @staticmethod
  def get_color(text: str, type: ColorType | str, modify_type: str = 'fg'):
    return '\n'.join([f'<style {modify_type}="{type}">{t}</style>' for t in (text or '').split('\n')])

  @staticmethod
  def print_formatted(text: str, sep: str = ' ', end: str = '\n', padding_left: int = 2):
    split_text = [''.ljust(padding_left) + line for line in text.split('\n')]
    try:
      print_formatted_text(HTML(xml_format('\n'.join(split_text))), sep=sep, end=end)
    except Exception as error:
      print('\n'.join(split_text), sep=sep, end=end)

  @staticmethod
  def print_color(text: str, type: ColorType, modify_type: str = 'fg', sep: str = ' ', end: str = '\n'):
    Color.print_formatted(Color.get_color(text, type, modify_type), sep=sep, end=end)

