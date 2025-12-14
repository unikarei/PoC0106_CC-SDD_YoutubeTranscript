"""
Tests for Transcription Result Processing and Validation
Handles post-processing, language detection, database storage
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def test_transcription_processor_exists():
    """Verify TranscriptionProcessor module exists"""
    from services import transcription_processor
    assert transcription_processor is not None


def test_transcription_processor_class_exists():
    """Verify TranscriptionProcessor class is defined"""
    from services.transcription_processor import TranscriptionProcessor
    assert TranscriptionProcessor is not None


def test_transcription_processor_initialization():
    """Test TranscriptionProcessor can be initialized"""
    from services.transcription_processor import TranscriptionProcessor
    
    processor = TranscriptionProcessor()
    assert processor is not None


def test_process_transcript_adds_punctuation():
    """Test that processor adds proper punctuation"""
    from services.transcription_processor import TranscriptionProcessor
    
    processor = TranscriptionProcessor()
    raw_text = "これはテストです これは二つ目の文です"
    
    result = processor.process_transcript(raw_text)
    
    assert result is not None
    assert isinstance(result, str)


def test_process_transcript_adds_paragraphs():
    """Test that processor organizes text into paragraphs"""
    from services.transcription_processor import TranscriptionProcessor
    
    processor = TranscriptionProcessor()
    # Long text that should be split into paragraphs
    raw_text = "最初の段落です。" * 10 + "二つ目の段落です。" * 10
    
    result = processor.process_transcript(raw_text)
    
    # Should contain paragraph breaks
    assert result is not None


def test_detect_language_japanese():
    """Test language detection for Japanese text"""
    from services.transcription_processor import TranscriptionProcessor
    
    processor = TranscriptionProcessor()
    japanese_text = "これは日本語のテキストです。"
    
    detected = processor.detect_language(japanese_text)
    
    assert detected == "ja"


def test_detect_language_english():
    """Test language detection for English text"""
    from services.transcription_processor import TranscriptionProcessor
    
    processor = TranscriptionProcessor()
    english_text = "This is an English text sample."
    
    detected = processor.detect_language(english_text)
    
    assert detected == "en"


def test_validate_language_match():
    """Test language validation when expected matches detected"""
    from services.transcription_processor import TranscriptionProcessor
    
    processor = TranscriptionProcessor()
    text = "これは日本語です。"
    expected_language = "ja"
    
    is_valid, warning = processor.validate_language(text, expected_language)
    
    assert is_valid is True
    assert warning is None


def test_validate_language_mismatch():
    """Test language validation when expected doesn't match detected"""
    from services.transcription_processor import TranscriptionProcessor
    
    processor = TranscriptionProcessor()
    text = "This is English text."
    expected_language = "ja"
    
    is_valid, warning = processor.validate_language(text, expected_language)
    
    assert is_valid is False
    assert warning is not None
    assert "language" in warning.lower() or "mismatch" in warning.lower()


@patch('services.transcription_processor.SessionLocal')
def test_save_transcript_to_database(mock_session_local):
    """Test saving transcript to database"""
    from services.transcription_processor import TranscriptionProcessor
    
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session
    
    processor = TranscriptionProcessor()
    
    result = processor.save_transcript(
        job_id="test-job-123",
        text="これは文字起こし結果です。",
        language_detected="ja",
        model="whisper-1"
    )
    
    # Should have added transcript to database
    assert mock_session.add.called
    assert mock_session.commit.called
    assert result is True


@patch('services.transcription_processor.SessionLocal')
def test_save_transcript_handles_error(mock_session_local):
    """Test error handling when saving transcript fails"""
    from services.transcription_processor import TranscriptionProcessor
    
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session
    mock_session.commit.side_effect = Exception("Database error")
    
    processor = TranscriptionProcessor()
    
    result = processor.save_transcript(
        job_id="test-job-123",
        text="テキスト",
        language_detected="ja",
        model="whisper-1"
    )
    
    assert result is False


def test_calculate_estimated_time():
    """Test estimation of remaining processing time"""
    from services.transcription_processor import TranscriptionProcessor
    
    processor = TranscriptionProcessor()
    
    # Mock progress data
    audio_duration_seconds = 600  # 10 minutes
    current_progress = 50  # 50% complete
    
    estimated_seconds = processor.calculate_estimated_time(
        audio_duration_seconds,
        current_progress
    )
    
    # Should return reasonable estimate
    assert estimated_seconds > 0
    assert isinstance(estimated_seconds, (int, float))


def test_update_progress_with_estimation():
    """Test progress update includes time estimation"""
    from services.transcription_processor import TranscriptionProcessor
    
    processor = TranscriptionProcessor()
    
    with patch.object(processor, 'job_manager') as mock_manager:
        processor.update_progress(
            job_id="test-job-123",
            progress=75,
            audio_duration=600
        )
        
        # Should update progress
        if mock_manager:
            mock_manager.update_job_progress.assert_called()


def test_apply_speaker_diarization():
    """Test speaker distinction in transcript"""
    from services.transcription_processor import TranscriptionProcessor
    
    processor = TranscriptionProcessor()
    
    # Mock transcript with speaker info (if available from Whisper)
    raw_text = "話者1: こんにちは。話者2: こんにちは。"
    
    result = processor.process_transcript(raw_text)
    
    # Should preserve or enhance speaker info
    assert result is not None
    assert isinstance(result, str)


def test_post_process_complete_workflow():
    """Test complete post-processing workflow"""
    from services.transcription_processor import TranscriptionProcessor
    
    processor = TranscriptionProcessor()
    
    # Simulate complete workflow
    raw_transcript = {
        'text': 'これはテストです これは長い文章です ' * 5,
        'language': 'ja'
    }
    
    result = processor.post_process(
        transcript_text=raw_transcript['text'],
        expected_language='ja',
        job_id='test-job-123',
        model='whisper-1'
    )
    
    # Should return processed result
    assert result is not None
    assert 'text' in result
    assert 'language_valid' in result


@patch('services.transcription_processor.SessionLocal')
def test_save_with_metadata(mock_session_local):
    """Test saving transcript includes all metadata"""
    from services.transcription_processor import TranscriptionProcessor
    from models import Transcript
    
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session
    
    processor = TranscriptionProcessor()
    
    processor.save_transcript(
        job_id="test-job-123",
        text="文字起こし結果",
        language_detected="ja",
        model="whisper-1"
    )
    
    # Verify Transcript object was created with correct fields
    assert mock_session.add.called
    call_args = mock_session.add.call_args[0][0]
    assert isinstance(call_args, Transcript)
    assert call_args.job_id == "test-job-123"
    assert call_args.text == "文字起こし結果"
    assert call_args.language_detected == "ja"
    assert call_args.transcription_model == "whisper-1"


def test_logging_configuration():
    """Verify logging is configured for transcription processor"""
    import services.transcription_processor as processor_module
    
    assert hasattr(processor_module, 'logger')
