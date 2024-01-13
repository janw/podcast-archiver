from pathlib import Path
from unittest.mock import patch

import click
import pytest
from pydantic_core import Url

from podcast_archiver import __version__ as version
from podcast_archiver import cli


def test_main(tmp_path_cd: Path, feed_lautsprecher: Url) -> None:
    cli.main(["--feed", feed_lautsprecher, "-d", tmp_path_cd], standalone_mode=False)

    files = list(tmp_path_cd.glob("**/*.m4a"))
    assert len(files) == 5


def test_main_interrupted(tmp_path_cd: Path, feed_lautsprecher_notconsumed: Url) -> None:
    with patch("requests.sessions.Session.request", side_effect=KeyboardInterrupt), pytest.raises(SystemExit):
        cli.main(["--feed", feed_lautsprecher_notconsumed])

    files = list(tmp_path_cd.glob("*.m4a"))
    assert len(files) == 0


def test_main_nonexistent_dir(feed_lautsprecher_notconsumed: Url) -> None:
    with pytest.raises(SystemExit):
        cli.main(("--feed", feed_lautsprecher_notconsumed, "-d", "/nonexistent"))


def test_main_nonexistent_opml(tmp_path_cd: Path, feed_lautsprecher_notconsumed: Url) -> None:
    with pytest.raises(click.BadParameter, match="Field 'opml.0': Path does not point to a file"):
        cli.main(["--opml", "/nonexistent.xml"], standalone_mode=False)


@pytest.mark.parametrize("flag", ["-V", "--version"])
def test_main_print_version(flag: str, tmp_path_cd: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        cli.main([flag])

    captured = capsys.readouterr()

    assert captured.out.strip().endswith(version)
    files = list(tmp_path_cd.glob("*.m4a"))
    assert len(files) == 0


def test_main_unknown_arg(tmp_path_cd: Path, feed_lautsprecher_notconsumed: Url) -> None:
    with pytest.raises(SystemExit):
        cli.main(["--feedlings", feed_lautsprecher_notconsumed])

    files = list(tmp_path_cd.glob("*.m4a"))
    assert len(files) == 0


def test_main_no_args(tmp_path_cd: Path) -> None:
    with pytest.raises(SystemExit):
        cli.main([])

    files = list(tmp_path_cd.glob("**/*.m4a"))
    assert len(files) == 0


def test_main_config_file(tmp_path_cd: Path, feed_lautsprecher: Url) -> None:
    configfile = tmp_path_cd / "configtmp.yaml"
    configfile.write_text(f"feeds: [{feed_lautsprecher}]")

    cli.main(["--config", str(configfile), "-d", tmp_path_cd], standalone_mode=False)

    files = list(tmp_path_cd.glob("**/*.m4a"))
    assert len(files) == 5


def test_main_config_file_invalid(tmp_path_cd: Path, feed_lautsprecher_notconsumed: Url) -> None:
    configfile = tmp_path_cd / "configtmp.yaml"
    configfile.write_text("asdf blabl")

    with pytest.raises(click.BadParameter, match="File '.+/configtmp.yaml' is invalid"):
        cli.main(["--config", str(configfile)], standalone_mode=False)


def test_main_config_file_notfound(feed_lautsprecher_notconsumed: Url, capsys: pytest.CaptureFixture[str]) -> None:
    configfile = "/nonexistent/configtmp.yaml"

    with pytest.raises(click.BadParameter, match="File '/nonexistent/configtmp.yaml' does not exist"):
        cli.main(["--feed", feed_lautsprecher_notconsumed, "--config", str(configfile)], standalone_mode=False)


def test_main_config_file_generate(tmp_path_cd: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cli.main(["--config-generate"], standalone_mode=False)

    captured = capsys.readouterr()
    assert captured.out
    assert "# Field 'feeds': " in captured.out
    assert "feeds: []\n" in captured.out
    assert "# Field 'archive_directory': " in captured.out
    assert "archive_directory: null\n" in captured.out
