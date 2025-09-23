import requests
import re
from bs4 import BeautifulSoup, Tag
from unidecode import unidecode

from track.track_data import Lyrics

class Genius(Lyrics):
	def __init__(self) -> None:
		super().__init__(lyrics_url='https://www.genius.com/{artist}-{title}-lyrics')

	def get_url(self, artist: str, title: str) -> str:
		def format_text(text: str) -> str:
			return re.sub(r'-+', '-', re.sub(r'\W+', '-', re.sub(r'([\[(].+[)\]])|([\'"]+)', '', text))).lower()
		return unidecode(self.lyrics_url.format(
			artist=format_text(artist),
			title=format_text(title))
		)

	def get(self, artist: str, title: str) -> tuple[str | None, str]:
		url = self.get_url(artist, title)

		page = requests.get(url).text
		bs = BeautifulSoup(page, 'html.parser')
		html = bs.find('div', attrs={'id': 'lyrics-root'})
		if html is None:
			return None, url

		lyrics: list[str] = []
		containers: list[Tag] = html.find_all('div', attrs={'data-lyrics-container': "true"})
		for container in containers:
			to_remove: list[Tag] = container.find_all('div', attrs={'data-exclude-from-selection': "true"})
			for tag in to_remove:
				tag.decompose()

			for child in container.descendants:
				if hasattr(child, 'attrs'):
					continue
				lyrics.append(child.text)

		return self.format("\n".join(lyrics)), url