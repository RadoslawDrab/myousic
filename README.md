<h1>Myousic CLI</h1>

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
  - [1. Installing from GitHub Releases](#1-installing-from-github-releases)
  - [2. Building from source code](#2-building-from-source-code)
- [Configuration file](#configuration-file)
  - [Default](#default)
  - [Values](#values)
  - [Types](#types)
    - [`Search`](#search)
    - [`SearchList`](#searchlist)
    - [`Modifier`](#modifier)
    - [`UrlModifier`](#urlmodifier)
- [iTunes API Search](#itunes-api-search)
- [Download Workflow](#download-workflow)

## Overview

**Myousic** is a command-line interface (CLI) tool that allows you to:

1. **Download music** from YouTube using a provided YouTube link.
2. **Search for song metadata** (such as genre, artist, album, etc.) using the iTunes API.
3. **Manage the output and temporary storage** of downloaded files, including moving files to a specified folder and handling artwork.

The tool uses:

- **`yt_dlp`**: A powerful YouTube downloader and extractor.
- **`prompt_toolkit`**: For an interactive, user-friendly CLI interface.

## Features

- **Download music** directly from YouTube URLs with metadata included.
- **Search for song details** (e.g., artist, album, genre) in the iTunes database based on song metadata.
- **Flexible configuration** with options for customizing download and search behavior, genres, and more.

## Installation

You can install **Myousic** in two ways: either by downloading the latest release from GitHub or by building it from the source code.

### 1. Installing from GitHub Releases

1. Visit the [GitHub Releases page](https://github.com/RadoslawDrab/myousic/releases) for the latest version of **Myousic**.
2. Download the latest release package suitable for your operating system.

### 2. Building from source code

_Note_: You need to have Python installed on your system

1. Clone repository

```bash
git clone https://github.com/RadoslawDrab/myousic.git
cd myousic
```

2. Create virtual environment and install dependencies

```bash
# Creates virtual environment named 'dev'
python init.py --install dev
```

1. Build command

```bash
python init.py --build
```

Once installed, you can run the `myousic` command from the terminal:

```bash
myousic
```

It'll create `config.json` in your home directory

## Configuration file

### Default

`~/config.json`

```json
{
 "temp_folder": "~/tmp",
 "output_folder": "~/music",
 "artwork_size": 1000,
 "excluded_genres": [],
 "included_genres": [],
 "genres_modifiers": {}, 
  "lyrics_provider": "AzLyrics",
 "lyrics_modifiers": {},
 "lyrics_url_modifiers": {
  "artist": {},
  "title": {}
 },
 "genres_url_modifiers": {
  "artist": {},
  "title": {}
 },
 "show_count": 10
}
```

### Values

| Property             | Type                          | Description                                                                                                                                                                                      |
|:---------------------|:------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| temp_folder          | `str`                         | Temporary folder where downloaded files will be stored before being moved to the output folder.                                                                                                  |
| output_folder        | `str`                         | Folder where the final music files will be moved after download.                                                                                                                                 |
| artwork_size         | `int`                         | The maximum size (in pixels) of album artwork to download.                                                                                                                                       |
| excluded_genres      | [`SearchList`](#searchlist)   | A list of genres to exclude when searching or filtering music. This helps to narrow down results based on your preferences.                                                                      |
| included_genres      | [`SearchList`](#searchlist)  | A list of genres to include when searching for songs. Genres can be defined using regular expressions (e.g., "Rock$" to include all rock genres).                                                |
| genres_modifiers     | [`Modifier`](#modifier)       | A dictionary of regular expressions and their replacements to modify the genre field. For example, this could be used to map different versions of a genre name (e.g., Alt becomes Alternative). |
| lyrics_modifiers     | [`Modifier`](#modifier)       | An object that allows modification of lyrics-related metadata. This can be used to clean or adjust lyrics data.                                                                                  |
| lyrics_url_modifiers | [`UrlModifier`](#urlmodifier) | Modifiers for URLs related to lyrics fetching, such as cleaning up artist names by removing unwanted characters.                                                                                 |
| genres_url_modifiers | [`UrlModifier`](#urlmodifier) | Modifiers for genre-related URLs, typically used to clean up artist names or apply regex replacements for specific cases.                                                                        |
| lyrics_provider      | <code>list\[[Provider](#provider)\] \| [Provider](#provider) </code>        | Literal which allows user to change lyrics provider                                                                                                                                              |
| show_count           | `int`                         | Number of search results to display from the iTunes API when searching for a song.                                                                                                               |

### Types

#### `Search`

```python
str | re.Pattern
```

#### `SearchList`

```python
list[Search]
```

#### `Modifier`

```python
dict[Search, str]
```

#### `UrlModifier`

```python
{
  "title": Modifier,
  "artist": Modifier
}
```

#### `Provider`

```python
Literal['AzLyrics', 'LyricsOvh', 'Lyrist', 'Genius']
```

## iTunes API Search

The tool performs a search on iTunes using the song metadata (e.g., artist, title, album) extracted from YouTube. Based on the configuration settings, you can filter and modify the genres and lyrics of the song results.

You can define which genres to exclude and include in the search results.
Genres can be modified using regex patterns and mapped to your preferred genres.
The search results from iTunes will display the song title, artist, album, and artwork. You can select the most relevant result.

## Download Workflow

1. **YouTube Download**: The tool uses yt-dlp to download the song from YouTube. It supports both audio and video downloads, but the default behavior is to download only the audio.

2. **Search and Metadata**: After downloading, the tool queries the iTunes API to find metadata for the song. The metadata includes information such as the artist, album, and genre, which is displayed to the user.

3. **File Management**: Once the download is complete and the metadata is fetched, the file is moved from the temporary folder (tmp) to the specified music folder. If artwork is available, it will be saved with the song.

4. **Error Handling**: If no valid song is found on iTunes or if an error occurs during the download, the tool will notify the user and offer retry options.

