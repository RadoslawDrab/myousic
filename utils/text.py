import re

def uppercase(text: str, start_index: int = 0, span: int = 1):
  chunks = re.sub(r'\W', '-', text).split('-')
  new_text: str = ''
  for chunk in chunks:
    end_index = min(start_index + span, len(chunk)) if span > 0 else len(chunk)
    new_text += chunk[start_index : end_index].upper() + chunk[end_index:] + ' '
  return new_text.removesuffix(' ')