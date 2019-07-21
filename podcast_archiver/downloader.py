import urllib.error
from os import makedirs
from os import path
from os import remove
from shutil import copyfileobj
from urllib.request import Request
from urllib.request import urlopen

from podcast_archiver.constants import USER_AGENT


class PodcastDownloader:
    HEADERS = {"User-Agent": USER_AGENT}

    def __init__(self, podcast):
        self.podcast = podcast

    def download(self):
        pass

    def downloadPodcastFiles(self, linklist):
        if linklist is None or self._feed_title is None:
            return

        nlinks = len(linklist)
        if nlinks > 0:
            if self.verbose == 1:
                print("2. Downloading content ... ", end="")
            elif self.verbose > 1:
                print("2. Downloading content ...")

        for cnt, episode in enumerate(linklist):
            link = episode.url
            if self.verbose == 1:
                print(
                    "\r2. Downloading content ... {0}/{1}".format(cnt + 1, nlinks),
                    end="",
                    flush=True,
                )
            elif self.verbose > 1:
                print(
                    "\n\tDownloading file no. {0}/{1}:\n\t{2}".format(
                        cnt + 1, nlinks, link
                    )
                )

                if self.verbose > 2:
                    episode.print_info()

            if self.verbose > 1:
                print("\tLocal filename:", episode.filename)

            if path.isfile(episode.filename):
                if self.verbose > 1:
                    print("\t✓ Already exists.")
                continue

            # Begin downloading
            prepared_request = Request(link, headers=self._headers)
            try:
                with urlopen(prepared_request) as response:

                    # Check existence another time, with resolved link
                    link = response.geturl()
                    total_size = int(response.getheader("content-length", "0"))

                    # Create the subdir, if it does not exist
                    makedirs(path.dirname(episode.filename), exist_ok=True)

                    if self.progress and total_size > 0:
                        with open(episode.filename, "wb") as outfile:
                            self.prettyCopyfileobj(response, outfile)
                    else:
                        with open(episode.filename, "wb") as outfile:
                            copyfileobj(response, outfile)

                if self.verbose > 1:
                    print("\t✓ Download successful.")
            except (urllib.error.HTTPError, urllib.error.URLError) as error:
                if self.verbose > 1:
                    print("\t✗ Download failed. Query returned '%s'" % error)
            except KeyboardInterrupt:
                if self.verbose > 0:
                    print("\n\t✗ Unexpected interruption. Deleting unfinished file.")

                remove(episode.filename)
                raise

    def prettyCopyfileobj(self, fsrc, fdst, callback, block_size=8 * 1024):
        while True:
            buf = fsrc.read(block_size)
            if not buf:
                break
            fdst.write(buf)
            callback(len(buf))
