import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from services.playlist_expander import validate_youtube_url, expand_playlist_or_channel


def test_validate_youtube_url_accepts_youtube_domains():
    assert validate_youtube_url("https://www.youtube.com/playlist?list=abc").startswith("https://")
    assert validate_youtube_url("https://youtu.be/dQw4w9WgXcQ")


def test_validate_youtube_url_rejects_non_youtube():
    with pytest.raises(ValueError):
        validate_youtube_url("https://example.com")


@patch("services.playlist_expander.shutil.which", return_value="/usr/bin/yt-dlp")
@patch("services.playlist_expander.subprocess.run")
def test_expand_playlist_or_channel_parses_entries(mock_run, _mock_which):
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout='{"entries": [{"id": "abc", "title": "T1"}, {"webpage_url": "https://www.youtube.com/watch?v=def", "title": "T2"}]}' ,
        stderr="",
    )

    items = expand_playlist_or_channel("https://www.youtube.com/playlist?list=abc")
    assert items == [
        {"youtube_url": "https://www.youtube.com/watch?v=abc", "title": "T1"},
        {"youtube_url": "https://www.youtube.com/watch?v=def", "title": "T2"},
    ]


@patch("services.playlist_expander.shutil.which", return_value="/usr/bin/yt-dlp")
@patch("services.playlist_expander.subprocess.run")
def test_expand_playlist_or_channel_raises_on_failure(mock_run, _mock_which):
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="boom")

    with pytest.raises(RuntimeError):
        expand_playlist_or_channel("https://www.youtube.com/playlist?list=abc")
