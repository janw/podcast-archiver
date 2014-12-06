# Podcast Archiver

This python script takes the feed URL of your favorite podcast and downloads all available episodes to your computer. Even those files "hidden" in a paged feed will be tapped, so you'll have an entire backup of the series.

## Outline

In my experience, very few full-fledged podcast clients are able to access a paged feed (following IETF RFC5005), so only the last few episodes of a podcast will be available to download. When you discover a podcast that has been around for quite a while, you'll have a hard time to follow the "gentle listener's duty" and listen to the whole archive. The script in this repository is supposed to help you aquiring every last episode of your new listening pleasure.


## Usage

`podcast_archiver.py` takes command line arguments, containing for example the feeds that are supposed to be archived:

* `-f <url>` / `--feed=<url>`: Provide a feed-url that is to be archived. For example `-f http://freakshow.fm/feed/m4a/`.
* `-d <path>` / `--dir=<path`: Specify the output directory for the archive, denoted by `<path>`. If omitted, the files are written to the current directory. For example: `-d /Users/janwillhaus/Music/Podcasts`
* `-s` / `--subdirs`: Create subdirectories for the provided feeds. This option enables reading the title of the feed and saving the episodes to a subdir of that title (of course invalid characters are removed first).
* `-v` / `--verbose`: Increase verbose level. In level 1 for example all download paths are shown. By default, `podcast_archiver` shows basic output on how many episodes are downloaded and shows the progress on those. Multiple `v`'s each increase the verbosity (currently only level 1 is used)
