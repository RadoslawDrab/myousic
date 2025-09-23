import re

class Exit(BaseException): ...

def sanitize_filename(name: str):
	return re.sub(r'[\\/:;,\'"*?<>|]+', '_', name)