import pytest

from podcast_archiver.config import Settings
from podcast_archiver.models import Episode, FeedInfo
from podcast_archiver.utils import FilenameFormatter

FEED_INFO = FeedInfo(
    title="That\\Show",
    subtitle="The one that never comes/came to be",
    author="TheJanwShow",
    language="de-DE",
)


@pytest.mark.parametrize(
    "fname_tmpl,slugify,expected_fname",
    [
        (
            "{show.title}/{episode.published_time:%Y-%m-%d %H%M%S %Z} - {episode.title}.{ext}",
            False,
            "That-Show/2023-03-12 123456 UTC - Some Episode.mp3",
        ),
        (
            "{show.title}/{episode.published_time:%Y-%m-%d %H%M%S %Z} - {episode.title}.{ext}",
            True,
            "That-Show/2023-03-12-123456-UTC - Some-Episode.mp3",
        ),
        (
            "{show.author} - {show.subtitle}/{show.language} - {episode.published_time} - {episode.author}.{ext}",
            False,
            "TheJanwShow - The one that never comes-came to be/de-DE - 2023-03-12 - Janw.mp3",
        ),
        (
            "{show.author}--{show.subtitle}/{show.language}--{episode.published_time}--{episode.author}.{ext}",
            True,
            "TheJanwShow--The-one-that-never-comes-came-to-be/de-DE--2023-03-12--Janw.mp3",
        ),
        (
            "{show.author} -- {show.subtitle}/{episode.published_time} {episode.original_filename}",
            False,
            "TheJanwShow -- The one that never comes-came to be/2023-03-12 file.mp3",
        ),
    ],
)
def test_filename_formatting(fname_tmpl: str, slugify: bool, expected_fname: str, episode: Episode) -> None:
    settings = Settings(filename_template=fname_tmpl, slugify_paths=slugify)
    formatter = FilenameFormatter(settings=settings)

    result = formatter.format(episode, feed_info=FEED_INFO)

    assert str(result) == expected_fname
