# Podcast Archiver

[![Code Health](https://landscape.io/github/janwh/Podcast-Archiver/master/landscape.svg?style=flat)](https://landscape.io/github/janwh/Podcast-Archiver/master)
[![Code Climate](https://codeclimate.com/github/janwh/Podcast-Archiver/badges/gpa.svg)](https://codeclimate.com/github/janwh/Podcast-Archiver)
[![Issue Count](https://codeclimate.com/github/janwh/Podcast-Archiver/badges/issue_count.svg)](https://codeclimate.com/github/janwh/Podcast-Archiver)
[![Test Coverage](https://codeclimate.com/github/janwh/Podcast-Archiver/badges/coverage.svg)](https://codeclimate.com/github/janwh/Podcast-Archiver/coverage)

This python script takes the feed URL of your favorite podcast and downloads all available episodes to your computer. Even those files "hidden" in a paged feed will be tapped, so you'll have an entire backup of the series.

## Outline

In my experience, very few full-fledged podcast clients are able to access a paged feed (following IETF RFC5005), so only the last few episodes of a podcast will be available to download. When you discover a podcast that has been around for quite a while, you'll have a hard time to follow the "gentle listener's duty" and listen to the whole archive. The script in this repository is supposed to help you acquiring every last episode of your new listening pleasure.

Before downloading any episode the function first fetches all available pages of the feed and prepares a list. That way, you will never miss any episode.

## Requirements

`podcast_archiver.py` requires Python 3 (tested with 3.6), the [feedparser](https://github.com/kurtmckee/feedparser) library, and [tqdm](https://github.com/tqdm/tqdm) progress bar.

## Usage

`podcast_archiver.py` takes command line arguments, containing for example the feeds that are supposed to be archived:

* `-f <url>` / `--feed=<url>`: Provide a feed-url that is to be archived. `-f` can be used multiple times, so you may hand over more than one feed to archive. To keep everything neat and tidy, see the `-s` option down below.
* `-f <filename>` / `--feed=<filename>`: Provide one or multiple feed urls by providing a simple text file, containing one feed url per line. To keep everything neat and tidy, see the `-s` option down below.
* `-o <opml_filename>` / `--opml=<opml_filename>`: If you carry your podcast feeds in iTunes, Downcast, Overcast, or any other podcather that allows OPML export, you can reference the OPML filename right here, and Podcast Archiver will extract the feeds from there, without the need to use above-mentioned option `-f/--feed`.
* `-d <path>` / `--dir=<path`: Specify the output directory for the archive, denoted by `<path>`. If omitted, the files are written to the current directory.
* `-s` / `--subdirs`: Create subdirectories for the provided feeds. This option enables reading the title of the feed and saving the episodes to a subdir of that title (of course invalid characters are removed first).
* `-u` / `--update.`: Only update the archive. Meaning: The fetching of the feed pages (which can be slow at time) is interrupted when the first episode is detected that already has an audio file present in the archive. This option might be used, if you already have created an archive and just want to add the most recent (not yet downloaded) episode(s).
* `-v` / `--verbose`: Increase verbose level. In level 1 for example all download paths are shown. By default, `podcast_archiver` shows basic output on how many episodes are downloaded and shows the progress on those. Multiple `v`'s each increase the verbosity. By default the Archiver has no outputs at all, except for errors (perfect for cronjobs). Some approximate numbers on how talkative the Archiver gets by adding `v`s: Level 1 uses about 4 lines per entered podcast feed, Level 2 adds about 5 lines per episode, and Level 3 adds 2-10 lines per episode containing additional metadata.
* `-p` / `--progress`: Show a progress bar for episode downloads. Can be used in conjunction with `--verbose` (see above).
* `-S` / `--slugify`: Clean all folders and filename of potentially weird characters that might cause trouble with one or another target filesystem. The character set boils down to about: alphanumeric characters (both upper and lower case), dashes, and underscores, with unicode characters being normalized according to [Compatibility Decomposition](#excursion-unicode-normalization-in-slugify).
* '`-m <number_of_episodes>`', `--max-episodes=<number_of_episodes>`: Only download the given `<number_of_episodes>` per podcast feed. Useful if you don't really need the entire backlog. Keep in mind that with subsequent executions with new episodes appearing, Podcast Archiver will currently *not* remove previous episodes. Therefore the number of episodes on disk will increase (actually by a maximum of `<number_of_episodes>`) when new episodes start coming up in the feed, and the Archiver is run again.
* '`-n <name_of_episodes>`', `--name-episodes`: Adds Podcats and Episodes names to the downloaded files. Following the format: Podcast_Name - [Episode_Name]. *Attention* when used in conjunction with -S(slugify) argument it will remove [ ] from episode name.


### Full-fledged example
```
python3 podcast_archiver.py -d /Users/janwillhaus/Music/Podcasts -s \
    -f http://freakshow.fm/feed/m4a/ \
    -f http://alternativlos.org/alternativlos.rss \
    -f http://logbuch-netzpolitik.de/feed/m4a \
    -f http://not-safe-for-work.de/feed/m4a/ \
    -f http://raumzeit-podcast.de/feed/m4a/ \
    -f http://www.ard.de/static/radio/radiofeature/rss/podcast.xml \
    -f http://wir.muessenreden.de/feed/podcast/
```

### Process the feed list from a file

** Recently changed syntax **

If you have a larger list of podcasts and/or want to update the archive on a cronjob basis, the `-f` argument can be outsourced into a text file. The text file may contain one feed URL per line, looking like this:
```bash
python3 podcast_archiver.py -d ~/Music/Podcasts -s -u -f feedlist.txt
```

where `feedlist.txt` contains the URLs as if entered into the command line:
```
    http://freakshow.fm/feed/m4a/
    http://alternativlos.org/alternativlos.rss
    http://logbuch-netzpolitik.de/feed/m4a
    http://not-safe-for-work.de/feed/m4a/
    http://raumzeit-podcast.de/feed/m4a/
    http://www.ard.de/static/radio/radiofeature/rss/podcast.xml
    http://wir.muessenreden.de/feed/podcast/
```

This way, you can easily add and remove feeds to the list and let the archiver fetch the newest episodes for example by adding it to your crontab.

## Excursion: Unicode Normalization in Slugify

The `--slugify` option removes all ambiguous characters from folders and filenames used in the archiving process. The removal includes unicode normalization according to [Compatibility Decomposition](http://unicode.org/reports/tr15/tr15-18.html#Decomposition). What? Yeah, me too. I figured this is best seen in an example, so here's a fictitious episode name, and how it would be translated to an target filename using the Archiver:

```
SPR001_Umlaute sind ausschließlich in schönen Sprachen/Dialekten zu finden.mp3
```

will be turned into

```
SPR001_Umlaute-sind-ausschlielich-in-schonen-SprachenDialekten-zu-finden.mp3
```

Note that "decorated" characters like `ö` are replaced with their basic counterparts (`o`), while somewhat ligatur-ish ones like `ß` (amongst most unessential punctuation) are removed entirely.


## Todo

* Add ability to define a preferred format on feeds that contain links for multiple audio codecs.
* Add ability to define a range of episodes or time to download only episode from that point on or from there to the beginning or or or …
* Add ability to choose a prefix episodes with the episode number (rarely necessary, since most podcasts feature some kind of episode numbering in the filename)
* Add unittests
