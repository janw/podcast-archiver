import time

import pytest
from pydantic_core import Url

from podcast_archiver.models import Episode
from podcast_archiver.utils import MIMETYPE_EXTENSION_MAPPING

EPISODE_FIXTURE = {
    "title": "83: Linda Dong & Lia Napolitano on prototyping experience",
    "title_detail": {
        "type": "text/plain",
        "language": None,
        "base": "https://feeds.feedburner.com/debugshow",
        "value": "83: Linda Dong & Lia Napolitano on prototyping experience",
    },
    "summary": "Formerly on the Apple design prototype team that brought us, among other things, the Pencil, and the Siri experience team that put voices in our cars and televisions, Linda Dong and Lia Napolitano join Guy and Rene in a chat recorded right after WWDC 2016 in June… but saved as a special holiday gift for us all now. Grab a beverage and hit play!",
    "summary_detail": {
        "type": "text/html",
        "language": None,
        "base": "https://feeds.feedburner.com/debugshow",
        "value": "Formerly on the Apple design prototype team that brought us, among other things, the Pencil, and the Siri experience team that put voices in our cars and televisions, Linda Dong and Lia Napolitano join Guy and Rene in a chat recorded right after WWDC 2016 in June… but saved as a special holiday gift for us all now. Grab a beverage and hit play!",
    },
    "published": "Fri, 23 Dec 2016 09:55:09 -0500",
    "published_parsed": time.struct_time((2016, 12, 23, 14, 55, 9, 4, 358, 0)),
    "links": [
        {
            "length": "85468157",
            "type": "audio/mpeg",
            "href": "http://traffic.libsyn.com/zenandtech/debug83.mp3",
            "rel": "enclosure",
        }
    ],
    "id": "5A8152FA-82F0-4BF2-9F29-EC87A46DADD3",
    "guidislink": False,
    "authors": [{"name": "Linda Dong, Lia Napolitano, Guy English, Rene Ritchie"}],
    "author": "Linda Dong, Lia Napolitano, Guy English, Rene Ritchie",
    "author_detail": {"name": "Linda Dong, Lia Napolitano, Guy English, Rene Ritchie"},
    "subtitle": "Formerly on the Apple prototype team that brought us Pencil, and Siri experience team that put voices in cars and TV, Linda Dong and Lia Napolitano join Guy and Rene in a chat recorded after WWDC 2016 in June… but saved for now!",
    "subtitle_detail": {
        "type": "text/plain",
        "language": None,
        "base": "https://feeds.feedburner.com/debugshow",
        "value": "Formerly on the Apple prototype team that brought us Pencil, and Siri experience team that put voices in cars and TV, Linda Dong and Lia Napolitano join Guy and Rene in a chat recorded after WWDC 2016 in June… but saved for now!",
    },
    "content": [
        {
            "type": "text/plain",
            "language": None,
            "base": "https://feeds.feedburner.com/debugshow",
            "value": "Formerly on the Apple design prototype team that brought us, among other things, the Pencil, and the Siri experience team that put voices in our cars and televisions, Linda Dong and Lia Napolitano join Guy and Rene in a chat recorded right after WWDC 2016 in June… but saved as a special holiday gift for us all now. Grab a beverage and hit play!",
        }
    ],
    "image": {"href": "http://www.mobilenations.com/broadcasting/podcast_debug_1400.jpg"},
    "itunes_explicit": None,
}


def test_episode_validation() -> None:
    episode = Episode.model_validate(EPISODE_FIXTURE)

    assert episode.title == "83: Linda Dong & Lia Napolitano on prototyping experience"
    assert episode.media_link.href == Url("http://traffic.libsyn.com/zenandtech/debug83.mp3")
    assert episode.media_link.url == "http://traffic.libsyn.com/zenandtech/debug83.mp3"
    # assert episode.original_filename == "debug83.mp3"
    assert episode.ext == "mp3"


@pytest.mark.parametrize("mimetype,expected_ext", list(MIMETYPE_EXTENSION_MAPPING.items()))
def test_episode_missing_ext(mimetype: str, expected_ext: str) -> None:
    episode = Episode.model_validate(
        {
            "title": "83: …",
            "published_parsed": time.struct_time((2016, 12, 23, 14, 55, 9, 4, 358, 0)),
            "links": [
                {
                    "length": "85468157",
                    "type": mimetype,
                    "href": "http://traffic.libsyn.com/zenandtech/debug83",
                    "rel": "enclosure",
                }
            ],
        }
    )

    assert episode.media_link.url == "http://traffic.libsyn.com/zenandtech/debug83"
    # assert episode.original_filename == "debug83"
    assert episode.ext == expected_ext
