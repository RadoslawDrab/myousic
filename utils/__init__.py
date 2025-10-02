import re

class Exit(BaseException): ...

def sanitize_filename(name: str):
	return re.sub(r'[\\/:;,\'"*?<>|]+', '_', name)

class AttributeDict(dict):
	"""A dictionary that allows attribute-style access."""
	def __init__(self, *args, **kwargs):
		for key, value in kwargs.items():
			setattr(self, key, value)
		super().__init__(*args, **kwargs)