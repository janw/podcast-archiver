#!/usr/bin/env python

import feedparser
from urllib import request
import shutil
from os import path

savedir = path.expanduser('~/Music/Podcasts/Archive')

nextPage = 'http://freakshow.fm/feed/m4a/'
verbose = True

if verbose:
    print("1. Gathering link list ..", end="")

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

if verbose:
    print(" {0:d} links.\n2. Downloading content .."
                  .format(len(linklist)), end="")

for link in linklist:
    print(".", end="", flush=True)
    filename = path.join(savedir, path.basename(link))

    # Download the file from `url` and save it locally under `file_name`:
    with request.urlopen(link) as response, open(filename, 'wb') as outfile:
        shutil.copyfileobj(response, outfile)
