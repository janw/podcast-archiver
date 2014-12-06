#!/usr/bin/env python

import feedparser

nextPage = 'http://freakshow.fm/feed/m4a/'
verbose = True

if verbose: print("1. Gathering link list ..", end="")

linklist = []
while nextPage is not None:
    print(".", end="")
    feedobj = feedparser.parse(nextPage)

    nextPage = None
    for link in feedobj['feed']['links']:
        if link['rel'] == 'next':
            nextPage = link['href']
            break


    for episode in feedobj['items']:
        #print(episode['links'])

        for link in episode['links']:
            if link['type'] == 'audio/mp4':
                linklist.append(link['href'])

if verbose: print(" {0:d} links.\n2. Downloading content ..".format(len(linklist)))
