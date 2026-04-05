"""
Audio Extractor service tests
Tests verify YouTube audio extraction functionality
"""
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import yt_dlp

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def test_audio_extractor_service_exists():
    """Verify audio_extractor.py exists"""
    extractor_file = Path("backend/services/audio_extractor.py")
    assert extractor_file.exists(), "backend/services/audio_extractor.py must exist"


def test_audio_extraction_result_class():
    """Verify AudioExtractionResult dataclass is defined"""
    from services.audio_extractor import AudioExtractionResult

    result = AudioExtractionResult(
        success=True,
        file_path="/path/to/audio.m4a",
        duration_seconds=600,
        title="Test Video",
        error=None
    )

    assert result.success is True
    assert result.file_path == "/path/to/audio.m4a"
    assert result.duration_seconds == 600
    assert result.title == "Test Video"
    assert result.error is None


def test_audio_extraction_result_error_case():
    """Verify AudioExtractionResult handles error cases"""
    from services.audio_extractor import AudioExtractionResult

    result = AudioExtractionResult(
        success=False,
        file_path=None,
        duration_seconds=None,
        title=None,
        error="Video not found"
    )

    assert result.success is False
    assert result.file_path is None
    assert result.error == "Video not found"


def test_audio_extractor_class_exists():
    """Verify AudioExtractor class is defined"""
    from services.audio_extractor import AudioExtractor

    extractor = AudioExtractor()
    assert extractor is not None


def test_audio_extractor_has_extract_method():
    """Verify AudioExtractor has extract_audio method"""
    from services.audio_extractor import AudioExtractor

    extractor = AudioExtractor()
    assert hasattr(extractor, "extract_audio"), "AudioExtractor must have extract_audio method"


def test_validate_youtube_url_valid():
    """Verify URL validation for valid YouTube URLs"""
    from services.audio_extractor import AudioExtractor

    extractor = AudioExtractor()

    assert extractor.validate_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True
    assert extractor.validate_youtube_url("https://youtu.be/dQw4w9WgXcQ") is True
    assert extractor.validate_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s") is True


def test_validate_youtube_url_invalid():
    """Verify URL validation rejects invalid URLs"""
    from services.audio_extractor import AudioExtractor

    extractor = AudioExtractor()

    assert extractor.validate_youtube_url("https://example.com") is False
    assert extractor.validate_youtube_url("not a url") is False
    assert extractor.validate_youtube_url("") is False
    assert extractor.validate_youtube_url("https://youtube.com") is False


@patch('services.audio_extractor.yt_dlp.YoutubeDL')
def test_extract_audio_success_resolves_actual_output_extension(mock_ydl_class, tmp_path):
    """Test successful extraction resolves the actual downloaded output extension."""
    from services.audio_extractor import AudioExtractor

    mock_ydl = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl

    output_file = tmp_path / "job123.mp3"
    output_file.write_bytes(b"audio")

    mock_info = {
        'title': 'Test Video',
        'duration': 600,
        'id': 'test123',
        'ext': 'webm',
    }
    downloaded_info = {
        **mock_info,
        'requested_downloads': [{'filepath': str(output_file)}],
    }
    mock_ydl.extract_info.return_value = downloaded_info
    mock_ydl.prepare_filename.return_value = str(tmp_path / "job123.webm")

    with patch('services.audio_extractor.shutil.which', return_value='/usr/bin/ffmpeg'):
        extractor = AudioExtractor(output_dir=str(tmp_path))
    with patch.object(extractor, 'get_video_info', return_value=mock_info):
        result = extractor.extract_audio("https://www.youtube.com/watch?v=test123", "job123")

    assert result.success is True
    assert result.title == 'Test Video'
    assert result.duration_seconds == 600
    assert result.file_path == str(output_file)
    assert result.format == 'mp3'
    assert result.error is None


@patch('services.audio_extractor.yt_dlp.YoutubeDL')
def test_extract_audio_without_ffmpeg_keeps_original_container(mock_ydl_class, tmp_path, caplog):
    """Test extraction keeps the downloaded container when ffmpeg is unavailable."""
    from services.audio_extractor import AudioExtractor

    mock_ydl = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl

    output_file = tmp_path / "job123.webm"
    output_file.write_bytes(b"audio")

    mock_info = {
        'title': 'Test Video',
        'duration': 600,
        'id': 'test123',
        'ext': 'webm',
    }
    mock_ydl.extract_info.return_value = mock_info
    mock_ydl.prepare_filename.return_value = str(output_file)

    caplog.set_level(logging.WARNING)
    with patch('services.audio_extractor.shutil.which', return_value=None):
        extractor = AudioExtractor(output_dir=str(tmp_path))
    with patch.object(extractor, 'get_video_info', return_value=mock_info):
        result = extractor.extract_audio("https://www.youtube.com/watch?v=test123", "job123")

    assert result.success is True
    assert result.file_path == str(output_file)
    assert result.format == 'webm'
    assert 'ffmpeg not available' in caplog.text

    primary_opts = mock_ydl_class.call_args_list[0].args[0]
    assert primary_opts['format'] == 'bestaudio/best'
    assert 'postprocessors' not in primary_opts
    assert 'extract_audio' not in primary_opts


@patch('services.audio_extractor.yt_dlp.YoutubeDL')
def test_extract_audio_falls_back_to_android_progressive_download(mock_ydl_class, tmp_path):
    """Test 403 failures switch to android progressive fallback."""
    from services.audio_extractor import AudioExtractor

    primary_cm = MagicMock()
    primary_ydl = MagicMock()
    primary_cm.__enter__.return_value = primary_ydl

    fallback_cm = MagicMock()
    fallback_ydl = MagicMock()
    fallback_cm.__enter__.return_value = fallback_ydl

    mock_ydl_class.side_effect = [primary_cm, fallback_cm]

    video_info = {
        'title': 'Blocked Video',
        'duration': 2082,
        'id': 'd66vRhasiig',
        'ext': 'mp4',
    }
    primary_ydl.extract_info.side_effect = yt_dlp.DownloadError(
        "[0;31mERROR:[0m [youtube] d66vRhasiig: unable to download video data: HTTP Error 403: Forbidden"
    )

    output_file = tmp_path / "job123.mp4"
    output_file.write_bytes(b"video-bytes")
    fallback_ydl.extract_info.return_value = video_info
    fallback_ydl.prepare_filename.return_value = str(output_file)

    with patch('services.audio_extractor.shutil.which', return_value='/usr/bin/ffmpeg'):
        extractor = AudioExtractor(output_dir=str(tmp_path))
    with patch.object(extractor, 'get_video_info', return_value=video_info):
        result = extractor.extract_audio("https://www.youtube.com/watch?v=d66vRhasiig", "job123")

    assert result.success is True
    assert result.file_path == str(output_file)
    assert result.format == 'mp4'
    assert result.error is None

    fallback_opts = mock_ydl_class.call_args_list[1].args[0]
    assert fallback_opts['format'] == '18/best[ext=mp4]/best'
    assert fallback_opts['extractor_args']['youtube']['player_client'] == ['android']


@patch('services.audio_extractor.yt_dlp.YoutubeDL')
def test_extract_audio_sanitizes_colored_download_errors(mock_ydl_class, tmp_path):
    """Test failed downloads strip ANSI color codes from yt-dlp errors."""
    from services.audio_extractor import AudioExtractor

    primary_cm = MagicMock()
    primary_ydl = MagicMock()
    primary_cm.__enter__.return_value = primary_ydl

    fallback_cm = MagicMock()
    fallback_ydl = MagicMock()
    fallback_cm.__enter__.return_value = fallback_ydl

    mock_ydl_class.side_effect = [primary_cm, fallback_cm]

    video_info = {
        'title': 'Blocked Video',
        'duration': 2082,
        'id': 'd66vRhasiig',
        'ext': 'mp4',
    }
    colored_error = (
        "[0;31mERROR:[0m [youtube] d66vRhasiig: unable to download video data: "
        "HTTP Error 403: Forbidden"
    )
    primary_ydl.extract_info.side_effect = yt_dlp.DownloadError(colored_error)
    fallback_ydl.extract_info.side_effect = yt_dlp.DownloadError(colored_error)

    with patch('services.audio_extractor.shutil.which', return_value='/usr/bin/ffmpeg'):
        extractor = AudioExtractor(output_dir=str(tmp_path))
    with patch.object(extractor, 'get_video_info', return_value=video_info):
        result = extractor.extract_audio("https://www.youtube.com/watch?v=d66vRhasiig", "job123")

    assert result.success is False
    assert '' not in result.error
    assert 'HTTP Error 403: Forbidden' in result.error


@patch('services.audio_extractor.yt_dlp.YoutubeDL')
def test_extract_audio_invalid_url(mock_ydl_class):
    """Test audio extraction with invalid URL"""
    from services.audio_extractor import AudioExtractor

    extractor = AudioExtractor()
    result = extractor.extract_audio("https://invalid-url.com", "job123")

    assert result.success is False
    assert result.error is not None
    assert "invalid" in result.error.lower() or "url" in result.error.lower()


@patch('services.audio_extractor.yt_dlp.YoutubeDL')
def test_extract_audio_video_too_long(mock_ydl_class):
    """Test audio extraction fails for videos longer than 60 minutes"""
    from services.audio_extractor import AudioExtractor

    mock_ydl = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl

    mock_info = {
        'title': 'Long Video',
        'duration': 3700,
        'id': 'test123'
    }
    mock_ydl.extract_info.return_value = mock_info

    extractor = AudioExtractor()
    with patch.object(extractor, 'get_video_info', return_value=mock_info), patch.object(extractor, 'MAX_DURATION_SECONDS', 3600):
        result = extractor.extract_audio("https://www.youtube.com/watch?v=test123", "job123")

    assert result.success is False
    assert result.error is not None
    assert "60" in result.error or "limit" in result.error.lower()


@patch('services.audio_extractor.yt_dlp.YoutubeDL')
def test_extract_audio_handles_exceptions(mock_ydl_class):
    """Test audio extraction handles yt-dlp exceptions"""
    from services.audio_extractor import AudioExtractor

    extractor = AudioExtractor()
    with patch.object(extractor, 'get_video_info', side_effect=Exception("Network error")):
        result = extractor.extract_audio("https://www.youtube.com/watch?v=test123", "job123")

    assert result.success is False
    assert result.error is not None


def test_get_video_info_method_exists():
    """Verify AudioExtractor has get_video_info method"""
    from services.audio_extractor import AudioExtractor

    extractor = AudioExtractor()
    assert hasattr(extractor, "get_video_info"), "AudioExtractor must have get_video_info method"


@patch('services.audio_extractor.yt_dlp.YoutubeDL')
def test_get_video_info_success(mock_ydl_class):
    """Test getting video info without downloading"""
    from services.audio_extractor import AudioExtractor

    mock_ydl = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl

    mock_info = {
        'title': 'Test Video',
        'duration': 600,
        'thumbnail': 'https://example.com/thumb.jpg',
        'id': 'test123'
    }
    mock_ydl.extract_info.return_value = mock_info

    extractor = AudioExtractor()
    info = extractor.get_video_info("https://www.youtube.com/watch?v=test123")

    assert info is not None
    assert info['title'] == 'Test Video'
    assert info['duration'] == 600


def test_audio_output_directory_exists():
    """Verify audio output directory configuration"""
    from services.audio_extractor import AudioExtractor

    extractor = AudioExtractor()
    assert hasattr(extractor, "output_dir") or hasattr(extractor, "audio_dir"),         "AudioExtractor must have output directory configuration"
