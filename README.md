# Podcast Archiver

This python script takes the feed URL of your favorite podcast and downloads all available episodes to your computer. Even those files "hidden" in a paged feed will be tapped, so you'll have an entire backup of the series.

## Outline

In my experience, very few full-fledged podcast clients are able to access a paged feed (following IETF RFC5005), so only the last few episodes of a podcast will be available to download. When you discover a podcast that has been around for quite a while, you'll have a hard time to follow the "gentle listener's duty" and listen to the whole archive. The script in this repository is supposed to help you aquiring every last episode of your new listening pleasure.

Before downloading any episode the function first fetches all available pages of the feed and prepares a list. That way, you will never miss any episode.

## Requirements

`podcast_archiver.py` requires Python 3+ and the `feedparser` library (among others, which are installed with Python by default).

## Usage

`podcast_archiver.py` takes command line arguments, containing for example the feeds that are supposed to be archived:

* `-f <url>` / `--feed=<url>`: Provide a feed-url that is to be archived. `-f` can be used multiple times, so you may hand over more than one feed to archive. To keep everything neat and tidy, see the `-s` option down below.
* `-d <path>` / `--dir=<path`: Specify the output directory for the archive, denoted by `<path>`. If omitted, the files are written to the current directory.
* `-s` / `--subdirs`: Create subdirectories for the provided feeds. This option enables reading the title of the feed and saving the episodes to a subdir of that title (of course invalid characters are removed first).
* `-u` / `--update.`: Only update the archive. Meaning: The fetching of the feed pages (which can be slow at time) is interrupted when the first episode is detected that already has an audio file present in the archive. This option might be used, if you already have created an archive and just want to add the most recent (not yet downloaded) episode(s).
* `-v` / `--verbose`: Increase verbose level. In level 1 for example all download paths are shown. By default, `podcast_archiver` shows basic output on how many episodes are downloaded and shows the progress on those. Multiple `v`'s each increase the verbosity (currently only level 1 is used)

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

If you have a larger list of podcasts and/or want to update the archive on a cronjob basis, the `-f` argument can be outsourced into a text file like this:
```bash
python3 podcast_archiver.py -d ~/Music/Podcasts -s -u $(< feedlist.txt)
```

where `feedlist.txt contains the URLs as if entered into the command line:
```
    -f http://freakshow.fm/feed/m4a/ \
    -f http://alternativlos.org/alternativlos.rss \
    -f http://logbuch-netzpolitik.de/feed/m4a \
    -f http://not-safe-for-work.de/feed/m4a/ \
    -f http://raumzeit-podcast.de/feed/m4a/ \
    -f http://www.ard.de/static/radio/radiofeature/rss/podcast.xml \
    -f http://wir.muessenreden.de/feed/podcast/
```

This way, you can easily add and remove feeds to the list and let the archiver fetch the newest episodes whenever you you configure in your crontab.


## Todo

* Add ability to define a preferred format on feeds that contain links for multiple audio codecs.
* Add ability to define a range of episodes or time to download only episode from that point on or from there to the beginning or or or …
* Add ability to choose a prefix episodes with the episode number (rarely necessary, since most podcasts feature some kind of episode numbering in the filename)

## License

Copyright (c) 2014 Jan Willhaus

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
