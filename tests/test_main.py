from pathlib import Path
from unittest.mock import patch

import pytest

import podcast_archiver
from podcast_archiver.__main__ import main


def test_main(tmp_path_cd: Path, feed_lautsprecher):
    main(["--feed", feed_lautsprecher])

    files = list(tmp_path_cd.glob("*.m4a"))
    assert len(files) == 5


def test_main_interrupted(tmp_path_cd: Path, feed_lautsprecher_notconsumed):
    with patch("requests.sessions.Session.request", side_effect=KeyboardInterrupt), pytest.raises(SystemExit):
        main(["--feed", feed_lautsprecher_notconsumed])

    files = list(tmp_path_cd.glob("*.m4a"))
    assert len(files) == 0


def test_main_nonexistent_dir(feed_lautsprecher_notconsumed):
    with pytest.raises(SystemExit):
        main(("--feed", feed_lautsprecher_notconsumed, "-d", "/nonexistent"))


@pytest.mark.parametrize("flag", ["-V", "--version"])
@patch.object(podcast_archiver.__main__, "__version__", "123.4.5")
def test_main_print_version(flag, tmp_path_cd: Path, capsys):
    with pytest.raises(SystemExit):
        main([flag])

    captured = capsys.readouterr()

    assert captured.out == "123.4.5\n"
    files = list(tmp_path_cd.glob("*.m4a"))
    assert len(files) == 0


def test_main_unknown_arg(tmp_path_cd: Path, feed_lautsprecher_notconsumed):
    with pytest.raises(SystemExit):
        main(["--feedlings", feed_lautsprecher_notconsumed])

    files = list(tmp_path_cd.glob("*.m4a"))
    assert len(files) == 0


def test_main_no_args(tmp_path_cd: Path):
    with pytest.raises(SystemExit):
        main([])

    files = list(tmp_path_cd.glob("*.m4a"))
    assert len(files) == 0


def test_main_config_file(tmp_path_cd: Path, feed_lautsprecher):
    configfile = tmp_path_cd / "configtmp.yaml"
    configfile.write_text(f"feeds: [{feed_lautsprecher}]")

    main(["--config", str(configfile)])

    files = list(tmp_path_cd.glob("*.m4a"))
    assert len(files) == 5


def test_main_config_file_notfound(feed_lautsprecher_notconsumed, capsys):
    configfile = "/nonexistent/configtmp.yaml"

    with pytest.raises(SystemExit):
        main(["--feed", feed_lautsprecher_notconsumed, "--config", str(configfile)])

    captured = capsys.readouterr()
    assert "error: /nonexistent/configtmp.yaml does not exist" in captured.err


def test_main_config_file_generate(tmp_path_cd: Path):
    configfile = tmp_path_cd / "configtmp.yaml"

    with pytest.raises(SystemExit):
        main(["--config-generate", str(configfile)])

    content = configfile.read_text()
    assert content
    assert "## Field 'feeds': " in content
    assert "# feeds: []\n" in content
    assert "## Field 'archive_directory': " in content
    assert "# archive_directory: None\n" in content
