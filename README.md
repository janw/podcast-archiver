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

![Demo of podcast-archiver](.assets/demo.gif)

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

Podcast Archiver supports command line arguments, environment variables, and a config file to set it up. The most simple invocation, passing feeds as command line arguments, would like like this:

```sh
podcast-archiver --dir ~/Podcasts --feed https://feeds.feedburner.com/TheAnthropoceneReviewed
```

### What constitutes a "feed"

Podcast Archiver expects values to its `--feed/-f` argument to be URLs pointing to an [RSS feed of a podcast](https://archive.is/jYk3E).

If you are not certain if the link you have for a show that you like, you can try and pass it to Podcast Archiver directly. The archiver supports a variety of links from popular podcast players and platforms, including [Apple Podcasts](https://podcasts.apple.com/us/browse), [Overcast.fm](https://overcast.fm/), [Castro](https://castro.fm/), and [Pocket Casts](https://pocketcasts.com/):

```sh
# Archive from Apple Podcasts URL
podcast-archiver -f https://podcasts.apple.com/us/podcast/black-girl-gone-a-true-crime-podcast/id1556267741
# ... or just the ID
podcast-archiver -f 1556267741

# From Overcast podcast URL
podcast-archiver -f https://overcast.fm/itunes394775318/99-invisible
# ... or episode sharing links (will resolve to all episodes)
podcast-archiver -f https://overcast.fm/+AAyIOzrEy1g
```

#### Supported services

The table below lists most of the supported services and URLs. If you think that some service you like is missing here, [please let me know](https://github.com/janw/podcast-archiver/issues/new)!

| Service                               | Example URL                                                                            |
| ------------------------------------- | -------------------------------------------------------------------------------------- |
| Apple Podcasts                        | <https://podcasts.apple.com/us/podcast/the-anthropocene-reviewed/id1342003491>         |
| [Overcast](https://overcast.fm/)      | <https://overcast.fm/itunes394775318/99-invisible>, <https://overcast.fm/+AAyIOzrEy1g> |
| [Castro](https://castro.fm/)          | <https://castro.fm/podcast/f996ae94-70a2-4d9c-afbc-c70b5bacd120>                       |
| [SoundCloud](https://soundcloud.com/) | <https://soundcloud.com/chapo-trap-house>                                              |

#### Local files

Feeds can also be "fetched" from a local file:

```bash
podcast-archiver -f file:/Users/janw/downloaded_feed.xml
```

#### Testing without downloading

To find out if you have to the right feed, you may want to use the `--dry-run` option to output the discovered feed information and found episodes. It will prevent all downloads.

```sh
podcast-archiver -f https://feeds.feedburner.com/TheAnthropoceneReviewed --dry-run
```

### Using a config file

Podcast Archiver can be configured using a YAML config file as well. This way you can easily add and remove feeds to the list and let the archiver fetch the newest episodes, for example using a daily cronjob.

A simple config file can look like this:

```yaml
archive_directory: ~/Podcasts
filename_template: '{show.title}/{episode.published_time:%Y-%m-%d} - {episode.title}.{ext}'
write_info_json: true
feeds:
  - https://feeds.feedburner.com/TheAnthropoceneReviewed  # The Anthropocene Reviewed
  - https://feeds.megaphone.fm/heavyweight-spot  # Heavyweight
```

To create a config file, you may use `podcast-archiver --config-generate` to emit an example configuration locally. You can also find a [pre-populated config file here](https://github.com/janw/podcast-archiver/blob/main/config.yaml.example). The example config contains descriptions and default values for all available parameters. After modifying it to your liking, you can invoke the archiver by bassing the config file as a command line argument:

```sh
podcast-archiver --config config.yaml
```

Alternatively (for example, if you're running `podcast-archiver` in Docker), you may point it to the config file using the `PODCAST_ARCHIVER_CONFIG=path/to/config.yaml` environment variable.

If the `--config` parameter is omitted, the archiver will look for a config file in its app config directory. The location of this directory is OS-specific; it is printed with the `podcast-archiver --help` output (next to the `--config` option help text).

### Using environment variables

Most settings of Podcast Archiver are available as environment variables, too. Check `podcast-archiver --help` for options with `env var: …` next to them.

```sh
export PODCAST_ARCHIVER_FEEDS='https://feeds.feedburner.com/TheAnthropoceneReviewed'  # multiple must be space-separated
export PODCAST_ARCHIVER_ARCHIVE_DIRECTORY="$HOME/Podcasts"

podcast-archiver
```

## Advanced use

### Continuous mode

When the `--sleep-seconds` option is set to a non-zero value, Podcast Archiver operates in continuous mode. After successfully populating the archive, it will not terminate but rather sleep for the given number of seconds until it refreshes the feeds again and downloads episodes that have been published in the meantime.

If no new episodes have been published, no download attempts will be made, and the archiver will go to sleep again. This mode of operation is ideal to be run in a containerized setup, for example using [docker compose](https://docs.docker.com/compose/install/):

```yaml
services:
  podcast-archiver:
    restart: always
    image: ghcr.io/janw/podcast-archiver
    volumes:
      - ./archive:/archive
    command:
      - --sleep-seconds=3600  # sleep for 1 hour between updates
      - --feed=https://feeds.feedburner.com/TheAnthropoceneReviewed
      - --feed=https://feeds.megaphone.fm/heavyweight-spot
```

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

### All available options

Run `podcast-archiver --help` to see all available parameters and the corresponding environment variables.

![`podcast-archiver --help`](.assets/podcast-archiver-help.svg)
