from datetime import datetime, timezone
from pathlib import Path

import pytest

from podcast_archiver.config import Settings
from podcast_archiver.models import Episode, FeedInfo, Link
from podcast_archiver.utils import FilenameFormatter

EPISODE = Episode(
    title="Some Episode",
    subtitle="The unreleased version",
    author="Janw",
    published_parsed=datetime(2023, 3, 12, 12, 34, 56, tzinfo=timezone.utc),
    enclosure=Link(
        rel="enclosure",
        link_type="audio/mpeg",
        href="http://nowhere.invalid/file.mp3",
    ),
)
FEED_INFO = FeedInfo(
    title="That Show",
    subtitle="The one that never came to be",
    author="TheJanwShow",
    language="de-DE",
)


@pytest.mark.parametrize(
    "fname_tmpl,slugify,expected_fname",
    [
        (
            "{show.title}/{episode.published_time:%Y-%m-%d %H%M%S %Z} - {episode.title}.{ext}",
            False,
            "That Show/2023-03-12 123456 UTC - Some Episode.mp3",
        ),
        (
            "{show.author} - {show.subtitle}/{show.language} - {episode.published_time} - {episode.author}.{ext}",
            False,
            "TheJanwShow - The one that never came to be/de-DE - 2023-03-12 - Janw.mp3",
        ),
        (
            "{show.author}--{show.subtitle}/{show.language}--{episode.published_time}--{episode.author}.{ext}",
            True,
            "TheJanwShow--The-one-that-never-came-to-be/de-DE--2023-03-12--Janw.mp3",
        ),
        (
            "{show.author} -- {show.subtitle}/{episode.published_time} {episode.original_filename}",
            False,
            "TheJanwShow -- The one that never came to be/2023-03-12 file.mp3",
        ),
    ],
)
def test_filename_formatting(
    fname_tmpl: str, slugify: bool, expected_fname: str, default_settings_no_feeds: Settings
) -> None:
    default_settings_no_feeds.archive_directory = Path("")
    default_settings_no_feeds.filename_template = fname_tmpl
    default_settings_no_feeds.slugify_paths = slugify
    formatter = FilenameFormatter(settings=default_settings_no_feeds)

    result = formatter.format(EPISODE, feed_info=FEED_INFO)

    assert str(result) == expected_fname
