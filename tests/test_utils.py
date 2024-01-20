import pytest

from podcast_archiver.utils import truncate


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
