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


import argparse
import feedparser
from urllib.request import urlopen, Request
import urllib.error
from shutil import copyfileobj
from os import path, remove, makedirs, access, W_OK
from urllib.parse import urlparse
import unicodedata
import re
import xml.etree.ElementTree as etree


verbose = 1
savedir = ''
subdirs = False
update = False
maximumEpisodes = None

userAgent = 'Podcast-Archiver/0.4 (https://github.com/janwh/podcast-archiver)'
headers = {'User-Agent': userAgent}
feedparser.USER_AGENT = userAgent


class writeable_dir(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = values
        if not path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError("writeable_dir:{0} is not a valid path"
                                             .format(prospective_dir))
        if access(prospective_dir, W_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise argparse.ArgumentTypeError("writeable_dir:{0} is not a writeable dir"
                                             .format(prospective_dir))


def slugifyString(filename):
    filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore')
    filename = re.sub('[^\w\s\-\.]', '', filename.decode('ascii')).strip()
    filename = re.sub('[-\s]+', '-', filename)

    return filename


def linkToTargetFilename(link, feedtitle):

    # Remove HTTP GET parameters from filename by parsing URL properly
    linkpath = urlparse(link).path
    basename = path.basename(linkpath)

    # If requested, slugify the filename
    if slugify:
        basename = slugifyString(basename)
        feedtitle = slugifyString(feedtitle)
    else:
        basename.replace(path.pathsep, '_')
        basename.replace(path.sep, '_')
        feedtitle.replace(path.pathsep, '_')
        feedtitle.replace(path.sep, '_')

    # Generate local path and check for existence
    if subdirs:
        filename = path.join(savedir, feedtitle, basename)
    else:
        filename = path.join(savedir, basename)

    return filename


def parseFeedToNextPage(feedobj):

    # Assuming there will only be one link declared as 'next'
    nextPage = [link['href'] for link in feedobj['feed']['links'] if link['rel'] == 'next']
    if len(nextPage) > 0:
        nextPage = nextPage[0]
    else:
        nextPage = None

    return nextPage


def parseFeedToLinks(feedobj):

    # Try different feed episode layouts: 'items' or 'entries'
    episodeList = feedobj.get('items', False) or feedobj.get('entries', False)
    if episodeList:
        linklist = [parseEpisode(episode) for episode in episodeList]
        linklist = [link for link in linklist if link is not None]
    else:
        linklist = []

    return linklist


def parseEpisode(episode):
    url = None
    for link in episode['links']:
        if 'type' in link.keys():
            if link['type'].startswith('audio'):
                url = link['href']
            elif link['type'].startswith('video'):
                url = link['href']

    return url


def parseOpmlFile(opml):
    with opml as file:
        tree = etree.fromstringlist(file)

        feedlist = [node.get('xmlUrl') for node
                    in tree.findall("*/outline/[@type='rss']")
                    if node.get('xmlUrl') is not None]

        return feedlist


def main():
    global verbose
    global savedir
    global subdirs
    global update
    global slugify
    global maximumEpisodes

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
    parser.add_argument('-S', '--slugify', action='store_true',
                        help='''Clean all folders and filename of potentially weird
                             characters that might cause trouble with one or another
                             target filesystem.''')
    parser.add_argument('-m', '--max-episodes', type=int,
                        help='''Only download the given number of episodes per podcast
                             feed. Useful if you don't really need the entire backlog.''')

    args = parser.parse_args()

    verbose = args.verbose or 0
    if verbose > 2:
        print('Input arguments:', args)

    feedlist = []
    for feed in (args.feed or []):
        if path.isfile(feed):
            feedlist += open(feed, 'r').read().strip().splitlines()
        else:
            feedlist.append(feed)

    for opml in (args.opml or []):
        feedlist += parseOpmlFile(opml)

    savedir = args.dir or ''
    subdirs = args.subdirs
    update = args.update
    slugify = args.slugify
    maximumEpisodes = args.max_episodes or None

    if verbose > 1:
        print("Verbose level: ", verbose)

    if verbose > 0 and update:
        print("Updating archive")

    for feed in feedlist:
        if verbose > 0:
            print("\nDownloading archive for: " + feed)
        linklist, feedtitle = processPodcastLink(feed)
        downloadPodcastFiles(linklist, feedtitle)

    if verbose > 0:
        print("\nDone.")

    return


def processPodcastLink(link):
    if verbose > 0:
        print("1. Gathering link list ..", end="")

    feedtitle = None
    nextPage = link
    linklist = []
    while nextPage is not None:
        if verbose > 0:
            print(".", end="", flush=True)

        feedobj = feedparser.parse(nextPage)

        # Escape improper feed-URL
        if 'status' in feedobj.keys() and feedobj['status'] >= 400:
            print("\nQuery returned HTTP error", feedobj['status'])
            return None, None

        # Escape malformatted XML
        if feedobj['bozo'] == 1:

            # If the character encoding is wrong, we continue as long as the reparsing succeeded
            if type(feedobj['bozo_exception']) is not feedparser.CharacterEncodingOverride:
                print('\nDownloaded feed is malformatted on', nextPage)
                return None, None

        # Parse the feed object for episodes and the next page
        linklist += parseFeedToLinks(feedobj)
        nextPage = parseFeedToNextPage(feedobj)

        if feedtitle is None:
            feedtitle = feedobj['feed']['title']

        numberOfLinks = len(linklist)

        # On given option, run an update, break at first existing episode
        if update:
            for index, link in enumerate(linklist):
                filename = linkToTargetFilename(link, feedtitle)

                if path.isfile(filename):
                    del(linklist[index:])
                    break
            numberOfLinks = len(linklist)

        # On given option, crop linklist to maximum number of episodes
        if maximumEpisodes is not None and maximumEpisodes < numberOfLinks:
            linklist = linklist[0:maximumEpisodes]
            numberOfLinks = maximumEpisodes

        if maximumEpisodes is not None or update:
            break

    linklist.reverse()

    if verbose > 0:
        print(" %d episodes" % numberOfLinks)

    return linklist, feedtitle


def downloadPodcastFiles(linklist, feedtitle):
    if linklist is None or feedtitle is None:
        return

    nlinks = len(linklist)
    if nlinks > 0 and verbose > 0:
        print("2. Downloading content ...")

    for cnt, link in enumerate(linklist):
        if verbose == 1:
            print("\r\t{0}/{1}"
                  .format(cnt + 1, nlinks), end="", flush=True)
        elif verbose > 1:
            print("\n\tDownloading file no. {0}/{1}:\n\t{2}"
                  .format(cnt + 1, nlinks, link))

        # Check existence once ...
        filename = linkToTargetFilename(link, feedtitle)

        if verbose > 1:
            print("\tLocal filename:", filename)

        if path.isfile(filename):
            if verbose > 1:
                print("\t✓ Already exists.")
            continue

        # Begin downloading
        prepared_request = Request(link, headers=headers)
        try:
            with urlopen(prepared_request) as response:

                # Check existence another time, with resolved link
                link = response.geturl()
                filename = linkToTargetFilename(link, feedtitle)

                if verbose > 1:
                    print("\tLocal filename:", filename)

                if path.isfile(filename):
                    if verbose > 1:
                        print("\t✓ Already exists.")
                    continue

                # Create the subdir, if it does not exist
                makedirs(path.dirname(filename), exist_ok=True)

                with open(filename, 'wb') as outfile:
                    copyfileobj(response, outfile)
            print("\t✓ Download successful.")
        except (urllib.error.HTTPError,
                urllib.error.URLError) as error:
            print("\t✗ Download failed. Query returned '%s'" % error)
        except KeyboardInterrupt as error:
            print("\t✗ Unexpected interruption. Deleting unfinished file.")
            remove(filename)
            raise


if __name__ == "__main__":
    main()
