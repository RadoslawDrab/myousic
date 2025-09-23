from track.lyrics.AzLyrics import AzLyrics
from track.lyrics.LyricsOvh import LyricsOvh
from track.lyrics.Lyrist import Lyrist
from track.lyrics.Genius import Genius
from track.track_data import Lyrics
from type.Config import LyricsProvider
from typing import overload, TypeVar

Provider = TypeVar('Provider', bound=Lyrics)

@overload
def map_provider(name: LyricsProvider | str) -> Provider | None: ...
@overload
def map_provider(name: LyricsProvider | str, default: Provider) -> Provider: ...
def map_provider(name: LyricsProvider | str, default: Provider | None = None):
	match name:
		case 'AzLyrics':
			return AzLyrics()
		case 'Lyrist':
			return Lyrist()
		case 'LyricsOvh':
			return LyricsOvh()
		case 'Genius':
			return Genius()
	return default