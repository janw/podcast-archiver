# Podcast Archiver

<!-- markdownlint-disable MD033 MD013 -->
<div align="center">

![Podcast Archiver Logo](.assets/icon.png)

[![version](https://img.shields.io/pypi/v/podcast-archiver.svg)](https://pypi.org/project/podcast-archiver/)
[![python](https://img.shields.io/pypi/pyversions/podcast-archiver.svg)](https://pypi.org/project/podcast-archiver/)
[![downloads](https://img.shields.io/pypi/dm/podcast-archiver)](https://pypi.org/project/podcast-archiver/)

[![Maintainability](https://api.codeclimate.com/v1/badges/1cdd7513333043558ee7/maintainability)](https://codeclimate.com/github/janw/podcast-archiver/maintainability)
[![codecov](https://codecov.io/gh/janw/podcast-archiver/branch/main/graph/badge.svg?token=G8WI2ZILRG)](https://codecov.io/gh/janw/podcast-archiver)
[![pre-commit.ci](https://results.pre-commit.ci/badge/github/janw/podcast-archiver/main.svg)](https://results.pre-commit.ci/latest/github/janw/podcast-archiver/main)

[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://docs.astral.sh/ruff/)
[![poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/docs/)
[![pre-commit](https://img.shields.io/badge/-pre--commit-f8b424?logo=pre-commit&labelColor=grey)](https://github.com/pre-commit/pre-commit)

</div>

A fast and simple command line client to archive all episodes from your favorite podcasts.

Podcast Archiver takes the feed URLs of your favorite podcasts and downloads all available episodes for you—even those "hidden" in [paged feeds](https://podlove.org/paged-feeds/). You'll end up with a complete archive of your shows. The archiver also supports updating an existing archive, so that it lends itself to be set up as a cronjob.

## Setup

Install via [pipx](https://pipx.pypa.io/stable/):

```bash
pipx install podcast-archiver
```

Or use it via Docker:

```bash
docker run --tty --rm ghcr.io/janw/podcast-archiver --help
```

## Usage

Run `podcast-archiver --help` for details on how to use it:

<!-- RICH-CODEX fake_command: "podcast-archiver --help" -->
![`poetry run podcast-archiver --help`](.assets/podcast-archiver-help.svg)

### Full-fledged example

```bash
podcast-archiver -d ~/Music/Podcasts \
    --subdirs \
    --date-prefix \
    --progress \
    --verbose \
    -f http://logbuch-netzpolitik.de/feed/m4a \
    -f http://raumzeit-podcast.de/feed/m4a/ \
    -f https://feeds.lagedernation.org/feeds/ldn-mp3.xml
```

### Process the feed list from a file

If you have a larger list of podcasts and/or want to update the archive on a cronjob basis, the `-f` argument can be outsourced into a text file. The text file may contain one feed URL per line, looking like this:

```bash
podcast-archiver -d ~/Music/Podcasts -s -u -f feedlist.txt
```

where `feedlist.txt` contains the URLs as if entered into the command line:

```text
    http://logbuch-netzpolitik.de/feed/m4a
    http://raumzeit-podcast.de/feed/m4a/
    https://feeds.lagedernation.org/feeds/ldn-mp3.xml
```

This way, you can easily add and remove feeds to the list and let the archiver fetch the newest episodes for example by adding it to your crontab.

### Using a config file

Command line arguments can be replaced with entries in a YAML configuration file. An example config can be generated with

```bash
podcast-archiver --config-generate path/to/config.yaml
```

After modifying the settings to your liking, `podcast-archiver` can be run with

```bash
podcast-archiver --config path/to/config.yaml
```

Alternatively (for example, if you're running `podcast-archiver` in Docker), you may point it to the config file using the `PODCAST_ARCHIVER_CONFIG=path/to/config.yaml` environment variable.

### Using environment variables

`podcast-archiver` uses [Pydantic](https://docs.pydantic.dev/latest/usage/settings/#parsing-environment-variable-values) to parse and validate its configuration. You can also prefix all configuration options (as used in the config file) with `PODCAST_ARCHIVER_` and export the results as environment variables to change the behavior, like so:

```bash
export PODCAST_ARCHIVER_FEEDS='[
    "http://raumzeit-podcast.de/feed/m4a/",
    "https://feeds.lagedernation.org/feeds/ldn-mp3.xml"
]'  # Must be a string of a JSON array
export PODCAST_ARCHIVER_SLUGIFY_PATHS=true
export PODCAST_ARCHIVER_VERBOSE=2
```

## Excursion: Unicode Normalization in Slugify

The `--slugify` option removes all ambiguous characters from folders and filenames used in the archiving process. The removal includes unicode normalization according to [Compatibility Decomposition](http://unicode.org/reports/tr15/tr15-18.html#Decomposition). What? Yeah, me too. I figured this is best seen in an example, so here's a fictitious episode name, and how it would be translated to an target filename using the Archiver:

```text
SPR001_Umlaute sind ausschließlich in schönen Sprachen/Dialekten zu finden.mp3
```

will be turned into

```text
SPR001_Umlaute-sind-ausschlielich-in-schonen-SprachenDialekten-zu-finden.mp3
```

Note that "decorated" characters like `ö` are replaced with their basic counterparts (`o`), while somewhat ligatur-ish ones like `ß` (amongst most unessential punctuation) are removed entirely.

## Todo

* Add ability to define a preferred format on feeds that contain links for multiple audio codecs.
* Add ability to define a range of episodes or time to download only episode from that point on or from there to the beginning or or or …
* Add ability to choose a prefix episodes with the episode number (rarely necessary, since most podcasts feature some kind of episode numbering in the filename)
* Add unittests
