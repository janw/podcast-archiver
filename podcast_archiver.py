#!/usr/bin/env python3
"""
Podcast Archiver v0.1: Feed parser for local podcast archive creation

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
"""


import argparse
import feedparser
from urllib.request import urlopen
import urllib.error
from shutil import copyfileobj
from os import path, remove, makedirs, access, W_OK
from urllib.parse import urlparse
import unicodedata
import re


verbose = 1
savedir = ''
filename = ''
subdirs = False
update = False


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


def main():
    global verbose
    global savedir
    global subdirs
    global update
    global slugify

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
        import xml.etree.ElementTree as etree
        with opml as file:
            tree = etree.fromstringlist(file)

            for node in tree.iter():
                if node.tag == 'outline':
                    if node.get('type') != 'rss':
                        continue

                    url = node.get('xmlUrl')
                    if url is None:
                        continue
                    else:
                        feedlist.append(node.get('xmlUrl'))

    savedir = args.dir or ''
    subdirs = args.subdirs
    update = args.update
    slugify = args.slugify

    if verbose > 1:
        print("Verbose level: ", verbose)

    if verbose > 0 and update:
        print("Updating archive")

    for feed in feedlist:
        if verbose > 0:
            print("\nDownloading archive for: " + feed)
        download_archive(feed)
    return


def download_archive(nextPage):
    global filename

    if verbose > 0:
        print("1. Gathering link list ..", end="")

    linklist = []
    feedtitle = None
    while nextPage is not None:
        print(".", end="", flush=True)
        feedobj = feedparser.parse(nextPage)

        # Escape improper feed-URL
        if 'status' in feedobj.keys() and feedobj['status'] == 404:
            print("\nQuery returned 404 (Not Found) on ", nextPage)
            return

        # Escape malformatted XML
        if feedobj['bozo'] == 1:
            print('\nDownloaded feed is malformatted on', nextPage)
            return

        nextPage = None

        if feedtitle is None:
            feedtitle = feedobj['feed']['title']

        for link in feedobj['feed']['links']:
            if link['rel'] == 'next':
                nextPage = link['href']
                break

        # Try different feed episode layouts. 1st: 'items'
        for episode in feedobj['items']:
            linklist.append(parse_episode(episode))

        linklist = [x for x in linklist if x is not None]

        # Try different feed episode layouts. 1st: 'entries'
        if len(linklist) == 0:
            for episode in feedobj['entries']:
                linklist.append(parse_episode(episode))

            linklist = [x for x in linklist if x is not None]

        # Exit gracefully when no episodes have been found
        if len(linklist) == 0:
            print("No audio items have been found.",
                  "Maybe we don't know the feed's audio MIME type yet?")
            print("Suggestions (as defined in the feed's 'links' field:)")
            for link in episode['links']:
                print(link["type"])
            return

        # On given option, run an update, break at first existing episode
        if update:
            curlenlinklist = len(linklist)

            for cnt, link in enumerate(linklist):
                filename = linkToTargetFilename(link, feedtitle)

                if path.isfile(filename):
                    del(linklist[cnt:])
                    break

            if len(linklist) != curlenlinklist:
                break

    linklist.reverse()
    nlinks = len(linklist)

    if nlinks == 0:
        if verbose > 0:
            print("Nothing to do.")
        return

    if (verbose > 0):
        print(" {0:d} episodes.\n2. Downloading content ... \n"
              .format(nlinks), end="")

    for cnt, link in enumerate(linklist):
        if verbose == 1:
            print("\r{0}/{1}"
                  .format(cnt + 1, nlinks), end="", flush=True)
        elif verbose > 1:
            print("\nDownloading file no. {0}/{1}:\n{2}"
                  .format(cnt + 1, nlinks, link), end="", flush=True)

        filename = linkToTargetFilename(link, feedtitle)

        if verbose > 1:
            print("\nLocal filename:", filename)

        if path.isfile(filename):
            continue

        # Create the subdir, if it does not exist
        makedirs(path.dirname(filename), exist_ok=True)

        # Begin downloading
        try:
            with urlopen(link) as response, open(filename, 'wb') as outfile:
                copyfileobj(response, outfile)
        except (urllib.error.HTTPError,
                urllib.error.URLError) as error:
            print("\n - Query returned", error, end="", flush=True)

    if verbose > 0:
        print("\n ... Done.")


def parse_episode(episode):
    url = None
    for link in episode['links']:
        if 'type' in link.keys():
            if link['type'].startswith('audio'):
                url = link['href']
            elif link['type'].startswith('video'):
                url = link['href']

    return url


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:

        # Delete the current (incomplete) file
        try:
            remove(filename)
        except FileNotFoundError:
            pass
        print("\nQuit early.")
