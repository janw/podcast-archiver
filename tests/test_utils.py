import pytest

from podcast_archiver.utils import sanitize_url, truncate


@pytest.mark.parametrize(
    "input_str,expected_output",
    [
        ("LS015 Der Sender bin ich", "LS015 Der Sender …"),
        ("LS015 Der Sender", "LS015 Der Sender"),
        ("LS015_Der_Sender_bin_ich", "LS015_Der_Sender_bi…"),
    ],
)
def test_truncate(input_str: str, expected_output: str) -> None:
    assert truncate(input_str, 20) == expected_output


@pytest.mark.parametrize(
    "url, expected_sanitized",
    [
        ("https://example.com", "https://example.com"),
        ("https://foo:bar@example.com/baz", "https://example.com/baz"),
        ("https://foo@example.com/baz?api-key=1234", "https://example.com/baz"),
    ],
)
def test_sanitize_url(url: str, expected_sanitized: str) -> None:
    assert sanitize_url(url) == expected_sanitized
