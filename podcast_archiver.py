#!/usr/bin/env python3
"""
Podcast Archiver v0.3: Feed parser for local podcast archive creation

Copyright (c) 2014-2017 Jan Willhaus

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
"""


import sys
import argparse
from argparse import ArgumentTypeError
import feedparser
from feedparser import CharacterEncodingOverride
from urllib.request import urlopen, Request
import urllib.error
from shutil import copyfileobj
from os import path, remove, makedirs, access, W_OK
from urllib.parse import urlparse
import unicodedata
import re
import xml.etree.ElementTree as etree


class writeable_dir(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = values
        if not path.isdir(prospective_dir):
            raise ArgumentTypeError("%s is not a valid path" % prospective_dir)
        if access(prospective_dir, W_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise ArgumentTypeError("%s is not a writeable dir" % prospective_dir)


class PodcastArchiver:

    _feed_title = ''
    _feedobj = None
    _feed_info_dict = {}

    _userAgent = 'Podcast-Archiver/0.4 (https://github.com/janwh/podcast-archiver)'
    _headers = {'User-Agent': _userAgent}
    _global_info_keys = ['author', 'language', 'link', 'subtitle', 'title', ]
    _episode_info_keys = ['author', 'link', 'subtitle', 'title', ]
    _date_keys = ['published', ]

    savedir = ''
    verbose = 0
    subdirs = False
    update = False
    progress = False
    maximumEpisodes = None

    feedlist = []

    def __init__(self):

        feedparser.USER_AGENT = self._userAgent

    def addArguments(self, args):

        # if type(args) is argparse.ArgumentParser:
        #     args = parser.parse_args()

        self.verbose = args.verbose or 0
        if self.verbose > 2:
            print('Input arguments:', args)

        for feed in (args.feed or []):
            self.addFeed(feed)

        for opml in (args.opml or []):
            self.parseOpmlFile(opml)

        if args.dir:
            self.savedir = args.dir

        self.subdirs = args.subdirs
        self.update = args.update
        self.progress = args.progress
        self.slugify = args.slugify
        self.maximumEpisodes = args.max_episodes or None

        if self.verbose > 1:
            print("Verbose level: ", self.verbose)

    def addFeed(self, feed):
        if path.isfile(feed):
            self.feedlist += open(feed, 'r').read().strip().splitlines()
        else:
            self.feedlist.append(feed)

    def parseOpmlFile(self, opml):
        with opml as file:
            tree = etree.fromstringlist(file)

        for feed in [node.get('xmlUrl') for node
                     in tree.findall("*/outline/[@type='rss']")
                     if node.get('xmlUrl') is not None]:

            self.addFeed(feed)

    def processFeeds(self):

        if self.verbose > 0 and self.update:
            print("Updating archive")

        for feed in self.feedlist:
            if self.verbose > 0:
                print("\nDownloading archive for: " + feed)
            linklist = self.processPodcastLink(feed)
            self.downloadPodcastFiles(linklist)

        if self.verbose > 0:
            print("\nDone.")

    def parseGlobalFeedInfo(self, feedobj=None):
        if feedobj is None:
            feedobj = self._feedobj

        self._feed_info_dict = {}
        if 'feed' in feedobj:
            for key in self._global_info_keys:
                self._feed_info_dict['feed_' + key] = feedobj['feed'].get(key, None)

        return self._feed_info_dict

    def slugifyString(filename):
        filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore')
        filename = re.sub('[^\w\s\-\.]', '', filename.decode('ascii')).strip()
        filename = re.sub('[-\s]+', '-', filename)

        return filename

    def linkToTargetFilename(self, link, title='', must_have_ext=False):

        # Remove HTTP GET parameters from filename by parsing URL properly
        linkpath = urlparse(link).path
        basename = path.basename(linkpath)

        _, ext = path.splitext(basename)
        if must_have_ext and not ext:
            return None

        if title:
            basename = title + ext

        # If requested, slugify the filename
        if self.slugify:
            basename = PodcastArchiver.slugifyString(basename)
            self._feed_title = PodcastArchiver.slugifyString(self._feed_title)
        else:
            basename = basename.replace(path.pathsep, '_')
            basename = basename.replace(path.sep, '_')
            self._feed_title = self._feed_title.replace(path.pathsep, '_')
            self._feed_title = self._feed_title.replace(path.sep, '_')

        # Generate local path and check for existence
        if self.subdirs:
            filename = path.join(self.savedir, self._feed_title, basename)
        else:
            filename = path.join(self.savedir, basename)

        return filename

    def parseFeedToNextPage(self, feedobj=None):

        if feedobj is None:
            feedobj = self._feedobj

        # Assuming there will only be one link declared as 'next'
        self._feed_next_page = [link['href'] for link in feedobj['feed']['links']
                                if link['rel'] == 'next']

        if len(self._feed_next_page) > 0:
            self._feed_next_page = self._feed_next_page[0]
        else:
            self._feed_next_page = None

        return self._feed_next_page

    def parseFeedToLinks(self, feed=None):

        if feed is None:
            feed = self._feedobj

        # Try different feed episode layouts: 'items' or 'entries'
        episodeList = feed.get('items', False) or feed.get('entries', False)
        if episodeList:
            linklist = [self.parseEpisode(episode) for episode in episodeList]
            linklist = [link for link in linklist if len(link) > 0]
        else:
            linklist = []

        return linklist

    def parseEpisode(self, episode):
        url = None
        episode_info = {}
        for link in episode['links']:
            if 'type' in link.keys():
                if link['type'].startswith('audio'):
                    url = link['href']
                elif link['type'].startswith('video'):
                    url = link['href']

                if url is not None:
                    for key in self._episode_info_keys + self._date_keys:
                        episode_info[key] = episode.get(key, None)
                    episode_info['url'] = url

        return episode_info

    def processPodcastLink(self, link):
        if self.verbose > 0:
            print("1. Gathering link list ...", end="", flush=True)

        self._feed_title = None
        self._feed_next_page = link
        first_page = True
        linklist = []
        while self._feed_next_page is not None:
            if self.verbose > 0:
                print(".", end="", flush=True)

            self._feedobj = feedparser.parse(self._feed_next_page)

            # Escape improper feed-URL
            if 'status' in self._feedobj.keys() and self._feedobj['status'] >= 400:
                print("\nQuery returned HTTP error", self._feedobj['status'])
                return None

            # Escape malformatted XML
            if self._feedobj['bozo'] == 1:

                # If the character encoding is wrong, we continue as long as the reparsing succeeded
                if type(self._feedobj['bozo_exception']) is not CharacterEncodingOverride:
                    print('\nDownloaded feed is malformatted on', self._feed_next_page)
                    return None

            if first_page:
                self.parseGlobalFeedInfo()
                first_page = False

            # Parse the feed object for episodes and the next page
            linklist += self.parseFeedToLinks(self._feedobj)
            self._feed_next_page = self.parseFeedToNextPage(self._feedobj)

            if self._feed_title is None:
                self._feed_title = self._feedobj['feed']['title']

            numberOfLinks = len(linklist)

            # On given option, run an update, break at first existing episode
            if self.update:
                for index, episode_dict in enumerate(linklist):
                    link = episode_dict['url']
                    filename = self.linkToTargetFilename(link, episode_dict.get('title'))

                    if path.isfile(filename):
                        del(linklist[index:])
                        break
                numberOfLinks = len(linklist)

            # On given option, crop linklist to maximum number of episodes
            if self.maximumEpisodes is not None and self.maximumEpisodes < numberOfLinks:
                linklist = linklist[0:self.maximumEpisodes]
                numberOfLinks = self.maximumEpisodes

            if self.maximumEpisodes is not None or self.update:
                break

        linklist.reverse()

        if self.verbose > 0:
            print(" %d episodes" % numberOfLinks)

        if self.verbose > 2:
            import json
            print('Feed info:\n%s\n' % json.dumps(self._feed_info_dict, indent=2))

        return linklist


    def downloadPodcastFiles(self, linklist):
        if linklist is None or self._feed_title is None:
            return

        nlinks = len(linklist)
        if nlinks > 0:
            if self.verbose == 1:
                print("2. Downloading content ... ", end="")
            elif self.verbose > 1:
                print("2. Downloading content ...")

        for cnt, episode_dict in enumerate(linklist):
            link = episode_dict['url']
            if self.verbose == 1:
                print("\r2. Downloading content ... {0}/{1}"
                      .format(cnt + 1, nlinks), end="", flush=True)
            elif self.verbose > 1:
                print("\n\tDownloading file no. {0}/{1}:\n\t{2}"
                      .format(cnt + 1, nlinks, link))

                if self.verbose > 2:
                    import json
                    print('\tEpisode info:')
                    for key in episode_dict.keys():
                        print("\t * %10s: %s" % (key, episode_dict[key]))

            # Check existence once ...
            filename = self.linkToTargetFilename(link, episode_dict.get('title'))

            if self.verbose > 1:
                print("\tLocal filename:", filename)

            if path.isfile(filename):
                if self.verbose > 1:
                    print("\t✓ Already exists.")
                continue

            # Begin downloading
            prepared_request = Request(link, headers=self._headers)
            try:
                with urlopen(prepared_request) as response:

                    # Check existence another time, with resolved link
                    link = response.geturl()
                    total_size = int(response.getheader('content-length', '0'))
                    new_filename = self.linkToTargetFilename(link, episode_dict.get('title'), must_have_ext=True)

                    if new_filename and new_filename != filename:
                        filename = new_filename
                        if self.verbose > 1:
                            print("\tResolved filename:", filename)

                        if path.isfile(filename):
                            if self.verbose > 1:
                                print("\t✓ Already exists.")
                            continue

                    # Create the subdir, if it does not exist
                    makedirs(path.dirname(filename), exist_ok=True)

                    if self.progress and total_size > 0:
                        from tqdm import tqdm
                        with tqdm(total=total_size, unit='B',
                                  unit_scale=True, unit_divisor=1024) as progress_bar:

                            with open(filename, 'wb') as outfile:
                                self.prettyCopyfileobj(response, outfile,
                                                       callback=progress_bar.update)
                    else:
                        with open(filename, 'wb') as outfile:
                            copyfileobj(response, outfile)

                if self.verbose > 1:
                    print("\t✓ Download successful.")
            except (urllib.error.HTTPError,
                    urllib.error.URLError) as error:
                if self.verbose > 1:
                    print("\t✗ Download failed. Query returned '%s'" % error)
            except KeyboardInterrupt:
                if self.verbose > 0:
                    print("\n\t✗ Unexpected interruption. Deleting unfinished file.")

                remove(filename)
                raise

    def prettyCopyfileobj(self, fsrc, fdst, callback, block_size=8 * 1024):
        while True:
            buf = fsrc.read(block_size)
            if not buf:
                break
            fdst.write(buf)
            callback(len(buf))


if __name__ == "__main__":
    try:

        parser = argparse.ArgumentParser()
        parser.add_argument('-o', '--opml', action='append', type=argparse.FileType('r'),
                            help='''Provide an OPML file (as exported by many other podcatchers)
                                 containing your feeds. The parameter can be used multiple
                                 times, once for every OPML file.''')
        parser.add_argument('-f', '--feed', action='append',
                            help='''Add a feed URl to the archiver. The parameter can be used
                                 multiple times, once for every feed.''')
        parser.add_argument('-d', '--dir', action=writeable_dir,
                            help='''Set the output directory of the podcast archive.''')
        parser.add_argument('-s', '--subdirs', action='store_true',
                            help='''Place downloaded podcasts in separate subdirectories per
                                 podcast (named with their title).''')
        parser.add_argument('-u', '--update', action='store_true',
                            help='''Force the archiver to only update the feeds with newly added
                                 episodes. As soon as the first old episode found in the
                                 download directory, further downloading is interrupted.''')
        parser.add_argument('-v', '--verbose', action='count',
                            help='''Increase the level of verbosity while downloading.''')
        parser.add_argument('-p', '--progress', action='store_true',
                            help='''Show progress bars while downloading episodes.''')
        parser.add_argument('-S', '--slugify', action='store_true',
                            help='''Clean all folders and filename of potentially weird
                                 characters that might cause trouble with one or another
                                 target filesystem.''')
        parser.add_argument('-m', '--max-episodes', type=int,
                            help='''Only download the given number of episodes per podcast
                                 feed. Useful if you don't really need the entire backlog.''')

        args = parser.parse_args()

        pa = PodcastArchiver()
        pa.addArguments(args)
        pa.processFeeds()
    except KeyboardInterrupt:
        sys.exit('\nERROR: Interrupted by user')
    except FileNotFoundError as error:
        sys.exit('\nERROR: %s' % error)
    except ArgumentTypeError as error:
        sys.exit('\nERROR: Your config is invalid: %s' % error)