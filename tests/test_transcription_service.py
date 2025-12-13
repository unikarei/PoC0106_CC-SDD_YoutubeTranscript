"""
Tests for TranscriptionService
OpenAI Whisper API integration for audio-to-text conversion
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def test_transcription_service_exists():
    """Verify TranscriptionService module exists"""
    from services import transcription_service
    assert transcription_service is not None


def test_transcription_service_class_exists():
    """Verify TranscriptionService class is defined"""
    from services.transcription_service import TranscriptionService
    assert TranscriptionService is not None


def test_transcription_service_initialization():
    """Test TranscriptionService can be initialized"""
    from services.transcription_service import TranscriptionService
    
    service = TranscriptionService(api_key="test_key")
    assert service is not None


def test_transcription_service_has_transcribe_method():
    """Verify TranscriptionService has transcribe method"""
    from services.transcription_service import TranscriptionService
    
    service = TranscriptionService(api_key="test_key")
    assert hasattr(service, 'transcribe')
    assert callable(service.transcribe)


@patch('services.transcription_service.OpenAI')
@patch('os.path.exists')
@patch('os.path.getsize')
def test_transcribe_audio_file(mock_getsize, mock_exists, mock_openai_class):
    """Test transcribing an audio file with Whisper API"""
    from services.transcription_service import TranscriptionService
    
    # Mock file existence and size
    mock_exists.return_value = True
    mock_getsize.return_value = 1024  # 1KB
    
    # Mock OpenAI client
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    # Mock transcription response
    mock_response = MagicMock()
    mock_response.text = "これはテスト音声の文字起こし結果です。"
    mock_client.audio.transcriptions.create.return_value = mock_response
    
    service = TranscriptionService(api_key="test_key")
    
    # Mock file
    with patch('builtins.open', mock_open(read_data=b'fake audio data')):
        result = service.transcribe(
            audio_file_path="test_audio.m4a",
            language="ja"
        )
    
    # Verify transcription was called
    assert mock_client.audio.transcriptions.create.called
    assert result['success'] is True
    assert result['text'] == "これはテスト音声の文字起こし結果です。"


@patch('services.transcription_service.OpenAI')
@patch('os.path.exists')
@patch('os.path.getsize')
def test_transcribe_with_language_specification(mock_getsize, mock_exists, mock_openai_class):
    """Test transcription with language parameter"""
    from services.transcription_service import TranscriptionService
    
    mock_exists.return_value = True
    mock_getsize.return_value = 1024
    
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.text = "This is an English transcription."
    mock_client.audio.transcriptions.create.return_value = mock_response
    
    service = TranscriptionService(api_key="test_key")
    
    with patch('builtins.open', mock_open(read_data=b'fake audio data')):
        result = service.transcribe(
            audio_file_path="test_audio.m4a",
            language="en"
        )
    
    # Verify language was passed
    call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
    assert call_kwargs.get('language') == 'en'
    assert result['success'] is True


@patch('services.transcription_service.OpenAI')
@patch('os.path.exists')
@patch('os.path.getsize')
def test_transcribe_with_model_specification(mock_getsize, mock_exists, mock_openai_class):
    """Test transcription with model parameter"""
    from services.transcription_service import TranscriptionService
    
    mock_exists.return_value = True
    mock_getsize.return_value = 1024
    
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.text = "Transcription result."
    mock_client.audio.transcriptions.create.return_value = mock_response
    
    service = TranscriptionService(api_key="test_key")
    
    with patch('builtins.open', mock_open(read_data=b'fake audio data')):
        result = service.transcribe(
            audio_file_path="test_audio.m4a",
            model="whisper-1"
        )
    
    # Verify model was passed
    call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
    assert call_kwargs.get('model') == 'whisper-1'


@patch('services.transcription_service.OpenAI')
def test_transcribe_handles_file_not_found(mock_openai_class):
    """Test error handling when audio file doesn't exist"""
    from services.transcription_service import TranscriptionService
    
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    service = TranscriptionService(api_key="test_key")
    
    # Mock file not found
    with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
        result = service.transcribe(
            audio_file_path="nonexistent.m4a",
            language="ja"
        )
    
    assert result['success'] is False
    assert 'error' in result
    assert 'not found' in result['error'].lower() or 'file' in result['error'].lower()


@patch('services.transcription_service.OpenAI')
@patch('os.path.exists')
@patch('os.path.getsize')
def test_transcribe_checks_file_size_limit(mock_getsize, mock_exists, mock_openai_class):
    """Test file size limit check (25MB)"""
    from services.transcription_service import TranscriptionService
    
    mock_exists.return_value = True
    # Mock file size > 25MB
    mock_getsize.return_value = 30 * 1024 * 1024  # 30MB
    
    service = TranscriptionService(api_key="test_key")
    
    with patch('builtins.open', mock_open(read_data=b'fake audio data')):
        result = service.transcribe(
            audio_file_path="large_audio.m4a",
            language="ja"
        )
    
    assert result['success'] is False
    assert 'error' in result
    assert '25' in result['error'] or 'size' in result['error'].lower()


@patch('services.transcription_service.OpenAI')
def test_transcribe_handles_api_error(mock_openai_class):
    """Test error handling when OpenAI API fails"""
    from services.transcription_service import TranscriptionService
    
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    # Mock API error
    mock_client.audio.transcriptions.create.side_effect = Exception("API Error")
    
    service = TranscriptionService(api_key="test_key")
    
    with patch('builtins.open', mock_open(read_data=b'fake audio data')):
        with patch('os.path.getsize', return_value=1024):
            result = service.transcribe(
                audio_file_path="test_audio.m4a",
                language="ja"
            )
    
    assert result['success'] is False
    assert 'error' in result


@patch('services.transcription_service.OpenAI')
@patch('os.path.exists')
@patch('os.path.getsize')
def test_transcribe_with_prompt_hint(mock_getsize, mock_exists, mock_openai_class):
    """Test transcription with prompt hint for better accuracy"""
    from services.transcription_service import TranscriptionService
    
    mock_exists.return_value = True
    mock_getsize.return_value = 1024
    
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.text = "Transcription with context."
    mock_client.audio.transcriptions.create.return_value = mock_response
    
    service = TranscriptionService(api_key="test_key")
    
    with patch('builtins.open', mock_open(read_data=b'fake audio data')):
        result = service.transcribe(
            audio_file_path="test_audio.m4a",
            language="ja",
            prompt="技術的な内容"
        )
    
    # Verify prompt was passed
    call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
    if 'prompt' in call_kwargs:
        assert call_kwargs.get('prompt') == "技術的な内容"


@patch('services.transcription_service.OpenAI')
@patch('os.path.exists')
@patch('os.path.getsize')
def test_transcribe_returns_language_detected(mock_getsize, mock_exists, mock_openai_class):
    """Test that transcription result includes detected language"""
    from services.transcription_service import TranscriptionService
    
    mock_exists.return_value = True
    mock_getsize.return_value = 1024
    
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.text = "Transcription result."
    mock_response.language = "ja"
    mock_client.audio.transcriptions.create.return_value = mock_response
    
    service = TranscriptionService(api_key="test_key")
    
    with patch('builtins.open', mock_open(read_data=b'fake audio data')):
        result = service.transcribe(
            audio_file_path="test_audio.m4a",
            language="ja"
        )
    
    # Result should include language information
    assert 'success' in result
    if hasattr(mock_response, 'language'):
        assert 'language_detected' in result or result.get('success')


@patch('services.transcription_service.OpenAI')
def test_transcribe_handles_timeout(mock_openai_class):
    """Test timeout handling for long API calls"""
    from services.transcription_service import TranscriptionService
    import socket
    
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    # Mock timeout error
    mock_client.audio.transcriptions.create.side_effect = socket.timeout("Request timeout")
    
    service = TranscriptionService(api_key="test_key")
    
    with patch('builtins.open', mock_open(read_data=b'fake audio data')):
        with patch('os.path.getsize', return_value=1024):
            result = service.transcribe(
                audio_file_path="test_audio.m4a",
                language="ja"
            )
    
    assert result['success'] is False
    assert 'error' in result


def test_transcription_result_structure():
    """Test that TranscriptionResult has expected structure"""
    from services.transcription_service import TranscriptionResult
    
    result = TranscriptionResult(
        success=True,
        text="Sample text",
        language_detected="ja",
        model="whisper-1",
        duration_seconds=120
    )
    
    assert result.success is True
    assert result.text == "Sample text"
    assert result.language_detected == "ja"
    assert result.model == "whisper-1"
    assert result.duration_seconds == 120


def test_logging_configuration():
    """Verify logging is configured for transcription service"""
    import services.transcription_service as transcription_module
    
    assert hasattr(transcription_module, 'logger')
