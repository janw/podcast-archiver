# Podcast Archiver

<!-- markdownlint-disable MD033 MD013 -->
<div align="center">

![Podcast Archiver Logo](.assets/icon.png)

[![version](https://img.shields.io/pypi/v/podcast-archiver.svg)](https://pypi.org/project/podcast-archiver/)
[![python](https://img.shields.io/pypi/pyversions/podcast-archiver.svg)](https://pypi.org/project/podcast-archiver/)
[![downloads](https://img.shields.io/pypi/dm/podcast-archiver)](https://pypi.org/project/podcast-archiver/)

[![Docker Build](https://github.com/janw/podcast-archiver/actions/workflows/docker-build.yaml/badge.svg)](https://ghcr.io/janw/podcast-archiver)
[![Tests](https://github.com/janw/podcast-archiver/actions/workflows/tests.yaml/badge.svg)](https://github.com/janw/podcast-archiver/actions/workflows/tests.yaml?query=branch%3Amain)
[![pre-commit.ci](https://results.pre-commit.ci/badge/github/janw/podcast-archiver/main.svg)](https://results.pre-commit.ci/latest/github/janw/podcast-archiver/main)

[![Maintainability](https://api.codeclimate.com/v1/badges/1cdd7513333043558ee7/maintainability)](https://codeclimate.com/github/janw/podcast-archiver/maintainability)
[![codecov](https://codecov.io/gh/janw/podcast-archiver/branch/main/graph/badge.svg?token=G8WI2ZILRG)](https://codecov.io/gh/janw/podcast-archiver)

[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://docs.astral.sh/ruff/)
[![poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/docs/)
[![pre-commit](https://img.shields.io/badge/-pre--commit-f8b424?logo=pre-commit&labelColor=grey)](https://github.com/pre-commit/pre-commit)

</div>

A fast and simple command line client to archive all episodes from your favorite podcasts.

Podcast Archiver takes the feed URLs of your favorite podcasts and downloads all available episodes for you—even those "hidden" in [paged feeds](https://podlove.org/paged-feeds/). You'll end up with a complete archive of your shows. The archiver also supports updating an existing archive, so that it lends itself to be set up as a cronjob.

⚠️ Podcast Archiver v1.0 completely changes the available command line options uses a new format for naming files (see [changing the filename format](#changing-the-filename-format) below). Using it on an existing pre-v1.0 folder structure will re-download all episodes unless you use an equivalent template. ⚠️

## Setup

Install via [pipx](https://pipx.pypa.io/stable/):

```bash
pipx install podcast-archiver
```

Install via [brew](https://brew.sh/):

```bash
brew install janw/tap/podcast-archiver
```

Or use it via Docker:

```bash
docker run --tty --rm ghcr.io/janw/podcast-archiver --help
```

By default, the docker image downloads episodes to a volume mounted at `/archive`.

## Usage

Run `podcast-archiver --help` for details on how to use it:

<!-- RICH-CODEX fake_command: "podcast-archiver --help" -->
![`poetry run podcast-archiver --help`](.assets/podcast-archiver-help.svg)

### Example invocation

```bash
podcast-archiver -d ~/Music/Podcasts \
    -f http://logbuch-netzpolitik.de/feed/m4a \
    -f http://raumzeit-podcast.de/feed/m4a/ \
    -f https://feeds.lagedernation.org/feeds/ldn-mp3.xml
```

This way, you can easily add and remove feeds to the list and let the archiver fetch the newest episodes for example by adding it to your crontab.

### Changing the filename format

Podcast Archiver has a `--filename-template` option that allows you to change the particular naming scheme of the archive. The default value for `--filename-template`. is shown in `podcast-archiver --help`, as well as all the available variables. The basic ones are:

* Episode: `episode.title`, `episode.subtitle`, `episode.author`, `episode.published_time`, `episode.original_filename`
* Podcast: `show.title`, `show.subtitle`, `show.author`, `show.language`

Note here that `episode.published_time` is a Python-native datetime, so its exact format can be adjusted further a la `{episode.published_time:%Y-%m-%d %H%M%S}` using [strftime-placeholders](https://strftime.org/). By default it uses `%Y-%m-%d` (e.g. 2024-12-31).

#### Examples

* More precise published time

  ```plain
  {show.title}/{episode.published_time:%Y-%m-%d %H%M%S %Z} - {episode.title}.{ext}
  ```

  Results in `…/That Show/2023-03-12 123456 UTC - Some Episode.mp3`

* Using the original filename (roughly equivalent to pre-1.0 `--subdirs`)

  ```plain
  {show.title}/{episode.original_filename}
  ```

  Results in `…/That Show/ts001-episodefilename.mp3`

* Using the original filename (roughly equivalent to pre-1.0 `--subdirs` + `--date-prefix`)

  ```plain
  {show.title}/{episode.published_time} {episode.original_filename}
  ```

  Results in `…/That Show/2023-03-12 ts001-episodefilename.mp3`

### Using a config file

Command line arguments can be replaced with entries in a YAML configuration file. An example config can be generated with

```bash
podcast-archiver --config-generate > config.yaml
```

After modifying the settings to your liking, `podcast-archiver` can be run with

```bash
podcast-archiver --config config.yaml
```

Alternatively (for example, if you're running `podcast-archiver` in Docker), you may point it to the config file using the `PODCAST_ARCHIVER_CONFIG=path/to/config.yaml` environment variable.

### Using environment variables

Some settings of Podcast Archiver are available as environment variables, too. Check `podcast-archiver --help` for options with `env var: …` next to them.
