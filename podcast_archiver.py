#!/usr/bin/env python
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


import sys
import getopt
import feedparser
from urllib.request import urlopen
import urllib.error
from shutil import copyfileobj
from os import path,remove,makedirs
from string import ascii_letters, digits


verbose = 1
savedir = ''
filename = ''
subdirs = False
update = False

def main():
    global verbose
    global savedir
    global subdirs
    global update
    # Parse input arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "f:d:vsu", [
                                   "feed=",
                                   "dir=",
                                   "verbose",
                                   "subdirs",
                                   "update"])
    except getopt.GetoptError as error:
        print("An error occured during input parsing: " + error.msg)
        return

    feedlist = []
    for opt in opts:
        if opt[0] == '-f' or opt[0] == '--feed':
            feedlist.append(opt[1])
        elif opt[0] == '-d' or opt[0] == '--dir':
            if path.isdir(opt[1]):
                savedir = opt[1]
            else:
                print("The provided directory does not exist")
                return
        elif opt[0] == '-v' or opt[0] == '--verbose':
            verbose += 1
        elif opt[0] == '-s' or opt[0] == '--subdirs':
            subdirs = True
        elif opt[0] == '-u' or opt[0] == '--update':
            update = True

    if verbose > 1:
        print("Verbose level: ", verbose-1)

    if verbose > 0 and update:
        print("Updating archive")

    for feed in feedlist:
        if verbose > 0:
            print("\nDownloading archive for: " + feed)
        download_archive(feed)
    return


def download_archive(nextPage):
    global savedir
    global filename

    if verbose > 0:
        print("1. Gathering link list ..", end="")

    linklist = []
    while nextPage is not None:
        print(".", end="", flush=True)
        feedobj = feedparser.parse(nextPage)

        # Escape improper feed-URL
        try:
            if feedobj['status'] == 404:
                print("\nQuery returned 404 (Not Found) on ", nextPage)
                return
        except:
            pass

        nextPage = None

        if len(linklist) == 0 and subdirs:

            # Get subdir name and sanitize it
            subdir = feedobj['feed']['title']
            subdir.replace(path.pathsep,'_')
            subdir.replace(path.sep,'_')

            curbasedir = path.join(savedir, subdir, '')

            # Create the subdir, if it does not exist
            if not path.isdir(curbasedir):
                makedirs(curbasedir)

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

                # Generate local path and check for existence
                if subdirs:
                    filename = path.join(curbasedir, path.basename(link))
                else:
                    filename = path.join(savedir, path.basename(link))
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
                  .format(cnt+1, nlinks), end="", flush=True)
        elif verbose > 1:
            print("\nDownloading file no. {0}/{1}:\n{2}"
                  .format(cnt+1, nlinks, link), end="", flush=True)

        # Generate local path and check for existence
        if subdirs:
            filename = path.join(curbasedir, path.basename(link))
        else:
            filename = path.join(savedir, path.basename(link))
        if path.isfile(filename):
            continue

        # Begin downloading
        try:
            with urlopen(link) as response, open(filename, 'wb') as outfile:
                copyfileobj(response, outfile)
        except urllib.error.HTTPError as error:
            print(" - Query returned", error, end="", flush=True)

    if verbose > 0:
            print("\n ... Done.")


def parse_episode(episode):
    url = None
    for link in episode['links']:
        if link['type'] == 'audio/mp4':
            url = link['href']
        elif link['type'] == 'audio/x-m4a':
            url = link['href']
        elif link['type'] == 'audio/mpeg':
            url = link['href']
        elif link['type'] == 'audio/mp3':
            url = link['href']
        elif link['type'] == 'audio/ogg':
            url = link['href']
        elif link['type'] == 'audio/oga':
            url = link['href']
        elif link['type'] == 'audio/opus':
            url = link['href']
        elif link['type'] == 'audio/x-mpeg':
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
