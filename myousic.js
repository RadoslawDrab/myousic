const { exec } = require('child_process')
const { copyrights, lineBreaker, question, errorPrompt, getCommands, readline } = require('./utils')

const BASE_URL = 'https://itunes.apple.com/search'

const KEYWORDS = [
	'clipboard',
	'open',
	'open-lyrics',
	'open-image',
	'url',
	'download',
	'other-genres',
	'add-lyrics',
	'downloadOnly'
]
const KEYWORD_VALUES = [
	'search',
	'url',
	'limit',
	'sort-artist',
	'sort-track',
	'sort-album',
	'sort-year',
	'artist',
	'track',
	'album',
	'year'
]

const SETTINGS = require('./settings.json')
const ARTWORK_SIZE = SETTINGS.ARTWORK_SIZE || 1000
const DEFAULT_AUDIO_FORMAT = SETTINGS.DEFAULT_AUDIO_FORMAT || 'm4a'
const MUSIC_FOLDER = SETTINGS.MUSIC_FOLDER || '~/Music/Music/Media.localized/Automatically Add to Music.localized/'
const ARTWORK_FORMAT = SETTINGS.ARTWORK_FORMAT || 'jpg'
const WINDOW_SCALING = SETTINGS.WINDOW_SCALING || 'auto'
const DEFAULT_LIMIT = SETTINGS.DEFAULT_LIMIT || 100
const EXAMPLE_DATA = {
	artistName: 'notFound',
	trackName: 'notFound',
	collectionName: 'notFound',
	trackTimeMillis: 100000,
	trackNumber: 1,
	trackCount: 1,
	discNumber: 1,
	discCount: 1,
	releaseDate: new Date().toISOString(),
	primaryGenreName: 'notFound',
	trackExplicitness: 'notFound'
}

const properties = getProperties()

let songNotFound = false
script()

async function script() {
	console.clear()
	// Gets data from the clipboard
	const clipboard = (await getCommands('pbpaste'))[0].value

	// Gets data from the clipboard if `clipboard` property is set
	const getFromClipboard = properties.clipboard && clipboard
	// Gets data from `search` property
	const getFromSearch = properties.search
	// Boolean which determines if url was set
	const getFromUrl = properties.url === true
	// Gets URL based on `url` property. Gets value from clipboard if `url` does not contain any url afterwards
	const url = getFromUrl ? clipboard : properties.url

	// Returns song name based on YouTube title
	const songName =
		properties.url &&
		(await getCommands(`yt-dlp --print "%(title)s" ${url}`))[0]?.value
			// Replaces anything that is contained inside of [] or ()
			?.replace(/\(.*\)|\[.*\]/gi, '')
			// Replaces any ' x ' to ', '
			.replace(/ x /gi, ', ')

	lineBreaker()
	// Gets term to search based on hierarchy: question after rerunned script > url > clipboard > search > no properties
	const term = songNotFound
		? await question('|  Song not found by YouTube name. New search: ')
		: '' || songName || getFromClipboard || getFromSearch || (await question('|  What to search: '))

	const attributes = {
		term,
		entity: 'song',
		// Allows to change limit
		limit: properties.limit?.replace(/\D/g) || DEFAULT_LIMIT
	}

	// Variable with every attiribute inside of `attributes` object formatted to math proper URI
	const formattedAttributes = Object.keys(attributes).reduce((str, attribute, i) => {
		// Gets encodedURI with current attribute
		const encodedAtt = encodeURIComponent(attributes[attribute])
		// Determines whether to add `&` and adds attribute to URI
		const att = `${i > 0 ? '&' : ''}${attribute}=${encodedAtt}`
		// Adds `att` to string only if `encodedAtt` is set
		return encodedAtt ? (str += att) : str
	}, '?')

	console.clear()
	// Fetches properly formatted URL
	fetch(BASE_URL + formattedAttributes)
		.then((response) => {
			// Checks whether script failed to get response. If so prints error to the console and returns
			if (!response.ok) {
				console.clear()
				const errorText = `ERROR\nCode: ${response.status}\nStatus: ${response.statusText}`
				errorPrompt(errorText)
				return
			}
			return response.json()
		})
		.then(async (data) => {
			function sort(a, b) {
				// Default searching from data received from iTunes
				let searchType = 'trackName'
				// All sort options
				const sortOptions = ['asc', 'desc']
				// Sets default sort option
				let sort = sortOptions[0]
				let prop = ''

				// Tests if property is a string and sets `prop` to proper property and `searchType` to type
				function setOptions(test, type) {
					if (typeof properties[test] === 'string') {
						prop = test
						searchType = type
					}
				}
				setOptions('sortAlbum', 'collectionName')
				setOptions('sortYear', 'releaseDate')
				setOptions('sortArtist', 'artistName')
				setOptions('sortTrack', 'trackName')

				// Checks if property exists
				if (typeof properties[prop] === 'string') {
					// Sets sorting option if found or set's default option
					sort = sortOptions.find((opt) => opt === properties[prop]) || sortOptions[0]
				}

				let sortDir = 1
				// If sorting is set to `desc` then order will reverse
				if (sort === 'desc') {
					sortDir *= -1
				}

				// Compares strings
				return a[searchType].localeCompare(b[searchType]) * sortDir
			}
			function filter(song) {
				const { track, artist, album, year } = properties
				const { trackName, artistName, collectionName, releaseDate } = song

				// Checks whether `trackName` includes anything from `track` property
				const sameTrack = track ? trackName.toLowerCase().includes(track.toLowerCase()) : true
				// Checks whether `artistName` includes anything from `artist` property
				const sameArtist = artist ? artistName.toLowerCase().includes(artist.toLowerCase()) : true
				// Checks whether `collectionName` includes anything from `album` property
				const sameAlbum = album ? collectionName.toLowerCase().includes(album.toLowerCase()) : true
				// Checks whether `releaseDate` includes anything from `year` property
				const sameYear = year ? (new Date(releaseDate).getFullYear().toString() || '').includes(year.toLowerCase()) : true
				// Returns true only if every property is truthy
				return sameTrack && sameArtist && sameAlbum && sameYear
			}

			// Returns if no data has been received
			if (!data) return

			// Gets results
			const { results } = data
			let songData = undefined

			let songId = 0

			// Gets sorted and filtered results
			const res = [...results].sort(sort).filter(filter)

			// If results contain array with more than one elements then formats proper display
			if (res.length > 1 && !properties.downloadOnly) {
				// Offset between last element and new column
				const offset = 7
				// Max number of width for track
				let maxWidth_track = 50
				// Max number of width for artist
				let maxWidth_artist = 25
				// Max number of width for album
				let maxWidth_collection = 30

				if (WINDOW_SCALING === 'auto') {
					const windowWidth = process.stdout.columns
					const availableWidth = windowWidth - 30 - offset * 3

					maxWidth_track = Math.round(availableWidth * 0.5)
					maxWidth_artist = Math.round(availableWidth * 0.25)
					maxWidth_collection = Math.round(availableWidth * 0.25)
				}

				// Adds new result for naming
				res.unshift({})

				const songs = res.reduce((prev, cur, id) => {
					// Returns properly formatted columns naming
					if (id === 0) {
						return (prev +=
							''.padEnd(5) +
							limitLength('Name', maxWidth_track) +
							'| ' +
							limitLength('Artist', maxWidth_artist) +
							'| ' +
							'Year'.padEnd(5) +
							'| ' +
							limitLength('Album', maxWidth_collection) +
							'\n|  ')
					}

					// Gets track name  with limited length to `maxWidth_track`
					const trackName = limitLength(cur.trackName, maxWidth_track)
					// Gets artist with limited length to `maxWidth_artist`
					const artistName = limitLength(cur.artistName, maxWidth_artist)
					// Gets album name with limited length to `maxWidth_collection`
					const collectionName = limitLength(cur.collectionName, maxWidth_collection)
					// Gets year value
					const year = (new Date(cur.releaseDate).getFullYear() || '').toString().padEnd(5)

					// Properly formatted string
					const song = trackName + '| ' + artistName + '| ' + year + '| ' + collectionName
					// Properly formatted id
					const songId = (id - 1).toString().padStart(3)
					// Returns new string
					return (prev += `${songId}: ${song}\n|  `)

					function limitLength(text, maxWidth) {
						// Checks whether text length is longer than `maxWidth`
						const isLongerThanMax = text.length > maxWidth
						// Adds '...' if `isLongerThanMax` is true
						return text
							.padEnd(maxWidth)
							.substring(0, maxWidth)
							.padEnd(maxWidth + (isLongerThanMax ? 3 : 0), '.')
							.padEnd(maxWidth + offset)
					}
				}, '|\n|  ')

				// Shows all songs
				console.clear()
				lineBreaker()
				console.log(songs)
				lineBreaker()

				res.shift()

				// Gets song id based on user input
				songId = +(await question('|  Which song to choose (ID): ')) || 0

				lineBreaker()
			}
			console.clear()

			// Gets song data
			songData = res[songId]

			// Checks if song has been found. If not reruns script
			if (songData === undefined) {
				songNotFound = true
				script()
				return
			}

			// Sets default data if `downloadOnly` property is set
			if (properties.downloadOnly) {
				const EXAMPLE = { ...EXAMPLE_DATA }
				EXAMPLE.trackName = songName
				songData = EXAMPLE
			}

			// Returns object containing all data
			const d = getData(songData)

			// Shows proper data prompt
			lineBreaker()
			console.log(d.prompt)
			copyrights()
			lineBreaker()

			// Opens lyrics and/or images if `open`, `openLyrics` or `openImage` property is set
			if (d.data.lyrics && (properties.open || properties.openLyrics)) exec(`open ${d.data.lyrics}`)
			if (d.data.artwork && (properties.open || properties.openImage)) exec(`open ${d.data.artwork}`)

			let message = ''
			// Downloads file if URL is provided and `download` property is set
			if (properties.download && url) {
				message = await downloadSong(url, d.data)
			}
			if (message) {
				console.log('|	' + message)
				lineBreaker()
			}
			// Closes readline
			readline.close()
			return
		})
	function getData(song) {
		const LYRICS_BASE_URL = 'https://www.azlyrics.com/lyrics/'
		const date = new Date(song.releaseDate)
		// Replaces 100x100 artwork format to desired resolution
		const artwork = song.artworkUrl100?.replace('100x100bb.jpg', `${ARTWORK_SIZE}x${ARTWORK_SIZE}bb.jpg`)
		// Returns properly formatted time of song
		const time = {
			minutes: Math.floor(song.trackTimeMillis / 1000 / 60)
				.toString()
				.padStart(2, '0'),
			seconds: Math.round((song.trackTimeMillis / 1000) % 60)
				.toString()
				.padStart(2, '0')
		}
		// Replaces everything inside of () with 'feat' or 'ft' inside
		const replaceRegex = new RegExp(/\(*(ft|feat).*/, 'gi')

		const artistName = song.artistName.replace(replaceRegex, '').replace(/\W/g, '')
		const trackName = song.trackName.replace(replaceRegex, '').replace(/\W/g, '')

		// Properly formats lyrics URL
		const lyrics = `${LYRICS_BASE_URL}${artistName}/${trackName}.html`.trim().toLowerCase()

		// Creates object with formatted data
		const formattedData = {
			name: song.trackName,
			artistName: song.artistName.replaceAll(' & ', ', '),
			album: song.collectionName,
			artwork,
			genre: song.primaryGenreName,
			date: date?.getFullYear(),
			time: `${time.minutes}:${time.seconds}`,
			lyrics,
			track: `${song.trackNumber}/${song.trackCount}`,
			disc: `${song.discNumber}/${song.discCount}`,
			trackExplicitness: song.trackExplicitness
		}
		// Creates properly formatted prompt
		const formattedPrompt = Object.keys(formattedData).reduce((acc, type) => {
			return (acc += `${type}: ${formattedData[type]}\n|  `)
		}, '|\n|  ')
		return { data: formattedData, prompt: formattedPrompt }
	}
}
async function downloadSong(url, song) {
	// Gets file format
	const format = properties.format || DEFAULT_AUDIO_FORMAT

	// Gets whole file name
	const musicFile = `${song.artistName} - ${song.name}.${format}`

	// Gets lyrics file
	const lyricsFile = `lyrics-${song.id}.txt`

	// Shows prompt and paste lyrics data into lyrics file
	if (properties.addLyrics) {
		await question('|  Copy lyrics and press Enter. ')
		await getCommands(`pbpaste > ${lyricsFile}`)
	}

	// Gets path to cover art
	const coverArtFile = `./artwork-${song.id}.${ARTWORK_FORMAT}`
	// Saves artwork to new file
	await getCommands(`curl --output ${coverArtFile} ${song.artwork}`)

	console.log('|  Downloading...')
	// Downloads file in proper format and with proper file name
	await getCommands(`yt-dlp -x -f ${format} --audio-quality 0 --add-metadata -o "${musicFile}" ${url}`)

	// Modifies metadata
	// priettier-ignore-start
	await getCommands(
		`exiftool 
    -title="${song.name}" 
    -artist="${song.artistName}" 
    -album="${song.album}" 
    -albumArtist="${song.artistName}" 
    "-coverArt<=${coverArtFile}" 
    -trackNumber="${song.track}" 
    -discNumber="${song.disc}" 
    -trackExplicitness="${song.trackExplicitness}" 
    -genre="${song.genre}" 
    -releaseDate="${song.date}" 
    -description="${url}"
		-longDescription="" 
		-comment=""
		-"lyrics<=${lyricsFile}"
    "${musicFile}"`
			.replaceAll(' \n', ' ')
			.replaceAll('\n', '')
	)
	// prietter-ignore-end

	// Removes cover art, lyrics and moves music to Music folder
	await getCommands(
		`rm -rf ${coverArtFile}`,
		`rm -rf *_original`,
		`rm -rf ${lyricsFile}`,
		`mv "./${musicFile}" ${MUSIC_FOLDER.replace(
			/\s/g,
			// prettier-ignore
			"\\ "
		)}`
	)
	return new Promise((resolve) => resolve('Download completed'))
}

function getProperties() {
	const keywords = [...KEYWORDS]
	const keywordValues = [...KEYWORD_VALUES]

	const props = {}

	keywords.forEach((keyword) => (props[formatTag(keyword)] = false))

	// Creates string out of arguments
	const args = process.argv.reduce((acc, val) => acc + ' ' + val, '')
	// Splits tags into array based on `--[tag]` and removes first one
	const allTags = args
		.trim()
		.split(/.(?=--\w*)/g)
		.slice(1)

	allTags
		// Filters to find tags only found in `keywords` array
		.filter((tag) => keywords.find((keyword) => '--' + keyword === tag))
		.forEach((tag) => {
			// Removes '--' string
			const formattedTag = tag.replaceAll('--', '')
			// Marks tag as `true`
			props[formatTag(formattedTag)] = true
		})
	allTags
		// Filters to find tags only found in `keywordValues` array
		.filter((tag) => keywordValues.find((keyword) => tag.includes('--' + keyword)))
		.forEach((tag) => {
			// Gets tag if it was set in `keywordValues` array
			const foundTag = keywordValues.find((keyword) => tag.includes('--' + keyword))
			// console.log(foundTag);
			// String to remove
			const toRemove = `--${foundTag} `
			// Gets value of the tag
			const value = tag.replace(toRemove, '')

			const hasValue = value !== toRemove.trim()
			if (!hasValue) return

			// Sets tag value
			props[formatTag(foundTag)] = value
		})

	return props
	function formatTag(keyword) {
		// Checks if tag includes minus. If so returns keyword
		if (!keyword.includes('-')) return keyword
		// Gets letter after '-'
		const letterToUpperCase = keyword.match(/(?<=\-)./g)
		// Replaces letter and minus with uppercase letter
		return keyword.replace(/-(?<=\-)./g, letterToUpperCase.toString().toUpperCase())
	}
}
