<h1 style="color:#7777ff">myousic</h1>

JS script to recognise and download music you want!

- [Introduction](#introduction)
- [Instalation](#instalation)
  - [Tools](#tools)
  - [Download](#download)
- [Usage](#usage)
  - [General options](#general-options)
- [Examples](#examples)
- [Configuration](#configuration)
  - [Options](#options)
  - [Schemes](#schemes)
    - [Introduction](#introduction-1)
    - [Setting](#setting)
    - [Examples](#examples-1)
- [Used tools](#used-tools)
- [Notes](#notes)

# Introduction

**Hey there!**

For a long time I've been downloading music using youtube and third party software.

However I found it time consuming, even few songs took a lot of time to import to Apple Music.

<br>

That's why I've challanged myself to create a script that could automatically do it for me.

It took a few days to make using `JavaScript` and `NodeJS`, but I've managed to accomplish my task.

I've also used `yt-dlp` for downloading from YouTube link and `exiftool` for changing metadata

# Instalation

## Tools

Tools to install:

1. [NodeJS](https://nodejs.org/en/)
2. [yt-dlp](https://github.com/yt-dlp/yt-dlp) (for downloading)
3. [exiftool](https://exiftool.org/) ([GitHub](https://github.com/exiftool/exiftool)) (for editing metadata)

## Download

<hr>

Download code from [GitHub](https://github.com/Radoslaw-Drab/myousic) or using [git](https://git-scm.com/):

1. Install git
2. In console (CLI) move to directory you want script to be saved to using `cd`
3. Type:

```bash
git clone https://github.com/Radoslaw-Drab/myousic
```

# Usage

```bash
node myousic.js [OPTIONS]
```

<br>

## General options

<hr>

Every option with argument has to be separated with space (quotation marks are optional, but preffered). Order does not matter.

Example:

```bash
node myousic.js --search "Linkin Park - Lost"
```

<br>

<table style="width:100%">
  <tr>
    <th style="width:30%">Option</th>
    <th>Argument</th>
    <th>Description</th>
  </tr>
  <tr>
    <td><code>--search</code></td>
    <td>string</td>
    <td>Searches for data based on input e.g. artist name and song title</td>
  </tr>
  <tr>
    <td><code>--url</code></td>
    <td>string</td>
    <td>Searches for data based on YouTube link</td>
  </tr>
  <tr>
    <td><code>--limit</code></td>
    <td>number</td>
    <td>Limits search (default 100, max 200)</td>
  </tr>
  <tr>
    <td><code>--sort-[TYPE]</code></td>
    <td><i>asc</i>, <i>desc</i></td>
    <td>Sorts output songs. <code>[TYPE]</code>: <i>artist</i>, <i>track</i>, <i>album</i>, <i>year</i></td>
  </tr>
  <tr>
    <td><code>--[TYPE]</code></td>
    <td>string</td>
    <td>Filters based on argument. <code>[TYPE]</code>: <i>artist</i>, <i>track</i>, <i>album</i>, <i>year</i></td>
  </tr>
  <tr>
    <td><code>--clipboard</code></td>
    <td>-</td>
    <td>Searches for data based on data inside of a clipboard</td>
  </tr>
  <tr>
    <td><code>--open</code></td>
    <td>-</td>
    <td>When song is found opens artwork and lyrics inside of default browser</td>
  </tr>
  <tr>
    <td><code>--open-lyrics</code></td>
    <td>-</td>
    <td>When song is found opens only lyrics inside of default browser</td>
  </tr>
  <tr>
    <td><code>--open-image</code></td>
    <td>-</td>
    <td>When song is found opens only artwork inside of default browser</td>
  </tr>
  <tr>
    <td><code>--url</code></td>
    <td>-</td>
    <td>Searches for data based on YouTube link in clipboard</td>
  </tr>
  <tr>
    <td><code>--download</code></td>
    <td>-</td>
    <td>Downloads music, changes metadata and moves to set folder. Works only with YouTube links, which means you have to use <code>--url</code> with this option</td>
  </tr>
  <tr>
    <td><code>--format</code></td>
    <td>string</td>
    <td>Changes default format</td>
  </tr>
  <tr>
    <td><code>--other-genres</code></td>
    <td>-</td>
    <td>Displays Genius website with other genres other than primary</td>
  </tr>
  <tr>
    <td><code>--add-genres</code></td>
    <td>-</td>
    <td>Before download asks to insert other genres to a song separated by space</td>
  </tr>
  <tr>
    <td><code>--add-lyrics</code></td>
    <td>-</td>
    <td>Before download asks to copy lyrics to clipboard and then adds it to music file</td>
  </tr>
</table>

# Examples

Search based on search input

```bash
node myousic.js --search "Linkin Park - Lost"
```

Search based on search input in clipboard (Data in clipboard: _Linkin Park - Lost_)

```bash
node myousic.js --clipboard
```

Search based on url

```bash
node myousic.js --url "https://youtu.be/7NK_JOkuSVY"
```

Search based on url with clipboard (Data in clipboard: _https://youtu.be/7NK_JOkuSVY_)

```bash
node myousic.js --url
```

Limits output data

```bash
node myousic.js --search "Linkin Park - Lost" --limit 20
```

Download song based on url with clipboard (Data in clipboard: _https://youtu.be/7NK_JOkuSVY_)

```bash
node myousic.js --url --download
```

Download song based on url with clipboard and opens lyrics (Data in clipboard: _https://youtu.be/7NK_JOkuSVY_)

```bash
node myousic.js --url --download --open-lyrics
```

Download song based on url with clipboard and opens lyrics and artwork (Data in clipboard: _https://youtu.be/7NK_JOkuSVY_)

```bash
node myousic.js --url --download --open
```

Sorts based on track in an ascending way

```bash
node myousic.js --search Linkin Park --sort-track asc
```

Sorts based on year in an descending way

```bash
node myousic.js --search Linkin Park --sort-year desc
```

Filters output which contains _'Linkin Park'_ as an artist.

```bash
node myousic.js --search Linkin Park --artist Linkin Park
```

Filters output which contains by _'Linkin Park'_ and was published in 2003.

```bash
node myousic.js --search Linkin Park --year 2003
```

Opens lyrics website and waits till user copies lyrics and presses enter. Then continuous download. (Data in clipboard: _https://youtu.be/7NK_JOkuSVY_)

```bash
node myousic.js --url --download --add-lyrics --open-lyrics
```

Then waits for the user action:

<img alt="Waiting for user interaction image" src="./img/add-lyrics.png" style="max-width: 1100px">

Opens genres website and waits till user adds genres and presses enter. Then continuous download. (Data in clipboard: _https://youtu.be/7NK_JOkuSVY_)

```bash
node myousic.js --url --download --add-genres
```

Then waits for the user action:

<img alt="Waiting for user interaction image" src="./img/add-genres.png" style="max-width: 1100px">

# Configuration

You can configure some options inside of `settings.json` file

## Options

| Option               | Description                                                                                            |
| -------------------- | ------------------------------------------------------------------------------------------------------ |
| ARTWORK_SIZE         | Size of artwork you would want your music to have (default 1000)                                       |
| ARTWORK_FORMAT       | Format of artwork (default jpg)                                                                        |
| DEFAULT_AUDIO_FORMAT | Format of audio (default m4a)                                                                          |
| MUSIC_FOLDER         | Folder where music will be saved (default ~/Downloads/)                                                |
| DEFAULT_LIMIT        | Default limit which will be set if not `--limit` option is set                                         |
| DEFAULT_OPTIONS      | String with options that will used by default. Example: `--url` will be used everytime you run command |
| SCHEMES              | See [Schemes](#schemes) section                                                                        |

<br>

In order to add files automatically to Apple Music locate folder named _Automatically Add To Music.localized_ and change `MUSIC_FOLDER` to path of this folder.

<hr>

## Schemes

<br>

### Introduction

<hr>

Creating schemes can be useful to set options everytime you'd like to repeat script usage.

<br>
Example:

You would like to download file, but everytime you need to add `--url`, `--download` or any other tag and you repeat the same command over and over again. That's where the schemes shine.

<br>

### Setting

<hr>

In `settings.json` file under _SCHEMES_ property you can define new schemes.

New scheme can be added by creating new string key which is the name of your scheme followed by value which contains string with all tags you desire to use separated by space.

<br>
Important

All scheme names have to start with capital letter

<br>

### Examples

<hr>

`settings.json`

```json
{
	// ...other settings
	"SCHEMES": {
		"MyScheme": "--url --download"
	}
}
```

Then:

```bash
node myousic.js MyScheme
```

which is an equivalent of:

```bash
node myousic.js --url --download
```

<br>
Other examples:

<br>

- Download with sorting by year descending

```json
"SCHEMES": {
  "YearDownload": "--url --download --sort-year desc"
}
```

- Download with lyrics

```json
"SCHEMES": {
  "LyricsDownload": "--url --download --open-lyrics --add-lyrics"
}
```

<br>

# Used tools

- VSCode
- [iTunes API](https://performance-partners.apple.com/search-api)

# Notes

For now script is optimised for MacOS only, however I'll try my best to make it available for Windows

<br>

Happy listening! 😁
