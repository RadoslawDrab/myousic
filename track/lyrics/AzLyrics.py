import requests
import re
from bs4 import BeautifulSoup
from unidecode import unidecode

from track.track_data import Lyrics

class AzLyrics(Lyrics):
	def __init__(self) -> None:
		super().__init__(lyrics_url='https://www.azlyrics.com/lyrics/{artist}/{title}.html')

	def get_url(self, artist: str, title: str) -> str:
		def format_text(text: str) -> str:
			return re.sub(r'[\[(].*[)\]]', '', re.sub(r'[ \'"]*', '', text)).lower()
		return unidecode(self.lyrics_url.format(
			artist=format_text(artist),
			title=format_text(title))
		)

	def get(self, artist: str, title: str) -> tuple[str | None, str]:
		url = self.get_url(artist, title)

		page = requests.get(url).text
		bs = BeautifulSoup(page, 'html.parser')
		html = bs.find('div', attrs={'class': 'ringtone'})

		if html is None:
			return None, url

		lyrics = html.find_next('div').text.strip()

		return self.format(lyrics), url