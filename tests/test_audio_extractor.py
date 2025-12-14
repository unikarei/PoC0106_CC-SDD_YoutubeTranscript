"""
Audio Extractor service tests
Tests verify YouTube audio extraction functionality
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def test_audio_extractor_service_exists():
    """Verify audio_extractor.py exists"""
    extractor_file = Path("backend/services/audio_extractor.py")
    assert extractor_file.exists(), "backend/services/audio_extractor.py must exist"


def test_audio_extraction_result_class():
    """Verify AudioExtractionResult dataclass is defined"""
    from services.audio_extractor import AudioExtractionResult
    
    # Test successful result
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
    
    # Test error result
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
    
    # Standard format
    assert extractor.validate_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True
    
    # Short format
    assert extractor.validate_youtube_url("https://youtu.be/dQw4w9WgXcQ") is True
    
    # With additional parameters
    assert extractor.validate_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s") is True


def test_validate_youtube_url_invalid():
    """Verify URL validation rejects invalid URLs"""
    from services.audio_extractor import AudioExtractor
    
    extractor = AudioExtractor()
    
    # Invalid URLs
    assert extractor.validate_youtube_url("https://example.com") is False
    assert extractor.validate_youtube_url("not a url") is False
    assert extractor.validate_youtube_url("") is False
    assert extractor.validate_youtube_url("https://youtube.com") is False


@patch('services.audio_extractor.yt_dlp.YoutubeDL')
def test_extract_audio_success(mock_ydl_class):
    """Test successful audio extraction"""
    from services.audio_extractor import AudioExtractor
    
    # Mock yt-dlp behavior
    mock_ydl = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl
    
    mock_info = {
        'title': 'Test Video',
        'duration': 600,
        'id': 'test123'
    }
    mock_ydl.extract_info.return_value = mock_info
    
    extractor = AudioExtractor()
    result = extractor.extract_audio("https://www.youtube.com/watch?v=test123", "job123")
    
    assert result.success is True
    assert result.title == 'Test Video'
    assert result.duration_seconds == 600
    assert result.file_path is not None
    assert result.error is None


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
    
    # Mock yt-dlp to return long video
    mock_ydl = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl
    
    mock_info = {
        'title': 'Long Video',
        'duration': 3700,  # 61 minutes
        'id': 'test123'
    }
    mock_ydl.extract_info.return_value = mock_info
    
    extractor = AudioExtractor()
    result = extractor.extract_audio("https://www.youtube.com/watch?v=test123", "job123")
    
    assert result.success is False
    assert result.error is not None
    assert "60" in result.error or "limit" in result.error.lower()


@patch('services.audio_extractor.yt_dlp.YoutubeDL')
def test_extract_audio_handles_exceptions(mock_ydl_class):
    """Test audio extraction handles yt-dlp exceptions"""
    from services.audio_extractor import AudioExtractor
    
    # Mock yt-dlp to raise exception
    mock_ydl = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.side_effect = Exception("Network error")
    
    extractor = AudioExtractor()
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
    
    # Mock yt-dlp behavior
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
    assert hasattr(extractor, "output_dir") or hasattr(extractor, "audio_dir"), \
        "AudioExtractor must have output directory configuration"
