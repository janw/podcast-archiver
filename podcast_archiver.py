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
from shutil import copyfileobj
from os import path


verbose = 1

def main():
    global verbose
    # Parse input arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "f:d:v",
                                   ["feed=", "dir=", "verbose"])
    except getopt.GetoptError as error:
        print("An error occured during input parsing: " + error.msg)
        return

    print(opts,args)
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
    print(feedlist)

    if verbose > 1:
        print("Verbose level: ", verbose-1)

    for feed in feedlist:
        if verbose > 0:
            print("Downloading archive for: " + feed)
        download_archive(feed)
    return


def download_archive(feed):
    if (verbose > 0): print("1. Gathering link list ..", end="")

    linklist = []
    while nextPage is not None:
        print(".", end="", flush=True)
        feedobj = feedparser.parse(nextPage)

        nextPage = None
        for link in feedobj['feed']['links']:
            if link['rel'] == 'next':
                nextPage = link['href']
                break

        for episode in feedobj['items']:
            for link in episode['links']:
                if link['type'] == 'audio/mp4':
                    linklist.append(link['href'])
                elif link['type'] == 'audio/mp3':
                    linklist.append(link['href'])
                elif link['type'] == 'audio/ogg':
                    linklist.append(link['href'])

    if (verbose > 0):
        print(" {0:d} episodes.\n2. Downloading content .."
              .format(len(linklist)), end="")

    for link in linklist:
        print(".", end="", flush=True)
        filename = path.join(savedir, path.basename(link))

        with urlopen(link) as response, open(filename, 'wb') as outfile:
            copyfileobj(response, outfile)


if __name__ == "__main__":
    main()

