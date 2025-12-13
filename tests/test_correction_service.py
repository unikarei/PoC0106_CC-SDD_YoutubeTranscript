"""
Tests for CorrectionService
OpenAI GPT-4o-mini integration for transcript correction
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def test_correction_service_exists():
    """Verify CorrectionService module exists"""
    from services import correction_service
    assert correction_service is not None


def test_correction_service_class_exists():
    """Verify CorrectionService class is defined"""
    from services.correction_service import CorrectionService
    assert CorrectionService is not None


def test_correction_service_initialization():
    """Test CorrectionService can be initialized"""
    from services.correction_service import CorrectionService
    
    service = CorrectionService(api_key="test_key")
    assert service is not None


def test_correction_service_has_correct_method():
    """Verify CorrectionService has correct method"""
    from services.correction_service import CorrectionService
    
    service = CorrectionService(api_key="test_key")
    assert hasattr(service, 'correct')
    assert callable(service.correct)


@patch('services.correction_service.OpenAI')
def test_correct_transcript_text(mock_openai_class):
    """Test correcting transcript with GPT-4o-mini"""
    from services.correction_service import CorrectionService
    
    # Mock OpenAI client
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    # Mock correction response
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "これは校正後のテキストです。誤字や文法が修正されました。"
    mock_response.choices = [MagicMock(message=mock_message)]
    mock_client.chat.completions.create.return_value = mock_response
    
    service = CorrectionService(api_key="test_key")
    
    result = service.correct(
        transcript_text="これは校正前のテキストです誤字や文法が間違ってます",
        language="ja"
    )
    
    # Verify correction was called
    assert mock_client.chat.completions.create.called
    assert result['success'] is True
    assert 'corrected_text' in result


@patch('services.correction_service.OpenAI')
def test_correct_with_japanese_prompt(mock_openai_class):
    """Test correction with Japanese-specific prompt"""
    from services.correction_service import CorrectionService
    
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "校正済みテキスト"
    mock_response.choices = [MagicMock(message=mock_message)]
    mock_client.chat.completions.create.return_value = mock_response
    
    service = CorrectionService(api_key="test_key")
    
    result = service.correct(
        transcript_text="テスト",
        language="ja"
    )
    
    # Verify Japanese correction prompt was used
    call_kwargs = mock_client.chat.completions.create.call_args[1]
    messages = call_kwargs['messages']
    
    # System message should mention Japanese correction
    assert any('日本語' in str(msg) or '誤変換' in str(msg) for msg in messages)


@patch('services.correction_service.OpenAI')
def test_correct_with_english_prompt(mock_openai_class):
    """Test correction with English-specific prompt"""
    from services.correction_service import CorrectionService
    
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Corrected English text."
    mock_response.choices = [MagicMock(message=mock_message)]
    mock_client.chat.completions.create.return_value = mock_response
    
    service = CorrectionService(api_key="test_key")
    
    result = service.correct(
        transcript_text="Test text",
        language="en"
    )
    
    # Verify English correction prompt was used
    call_kwargs = mock_client.chat.completions.create.call_args[1]
    messages = call_kwargs['messages']
    
    # System message should mention English correction
    assert any('English' in str(msg) or 'grammar' in str(msg) for msg in messages)


@patch('services.correction_service.OpenAI')
def test_correct_uses_gpt4o_mini(mock_openai_class):
    """Test that correction uses GPT-4o-mini model"""
    from services.correction_service import CorrectionService
    
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Corrected"
    mock_response.choices = [MagicMock(message=mock_message)]
    mock_client.chat.completions.create.return_value = mock_response
    
    service = CorrectionService(api_key="test_key")
    service.correct(transcript_text="Test", language="en")
    
    # Verify model parameter
    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs.get('model') == 'gpt-4o-mini'


@patch('services.correction_service.OpenAI')
def test_calculate_changes_summary(mock_openai_class):
    """Test generating summary of changes made"""
    from services.correction_service import CorrectionService
    
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "校正後テキスト"
    mock_response.choices = [MagicMock(message=mock_message)]
    mock_client.chat.completions.create.return_value = mock_response
    
    service = CorrectionService(api_key="test_key")
    
    original = "これはテストです"
    result = service.correct(transcript_text=original, language="ja")
    
    # Should include changes summary
    assert 'changes_summary' in result or 'corrected_text' in result


def test_generate_correction_prompt_japanese():
    """Test Japanese correction prompt generation"""
    from services.correction_service import CorrectionService
    
    service = CorrectionService(api_key="test_key")
    
    prompt = service._generate_correction_prompt("ja")
    
    assert prompt is not None
    assert '誤変換' in prompt or '句読点' in prompt or '日本語' in prompt


def test_generate_correction_prompt_english():
    """Test English correction prompt generation"""
    from services.correction_service import CorrectionService
    
    service = CorrectionService(api_key="test_key")
    
    prompt = service._generate_correction_prompt("en")
    
    assert prompt is not None
    assert 'grammar' in prompt.lower() or 'punctuation' in prompt.lower()


@patch('services.correction_service.OpenAI')
def test_correct_handles_api_error(mock_openai_class):
    """Test error handling when OpenAI API fails"""
    from services.correction_service import CorrectionService
    
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    # Mock API error
    mock_client.chat.completions.create.side_effect = Exception("API Error")
    
    service = CorrectionService(api_key="test_key")
    
    result = service.correct(
        transcript_text="テスト",
        language="ja"
    )
    
    assert result['success'] is False
    assert 'error' in result


@patch('services.correction_service.OpenAI')
def test_correct_handles_timeout(mock_openai_class):
    """Test timeout handling for long API calls"""
    from services.correction_service import CorrectionService
    import socket
    
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    # Mock timeout error
    mock_client.chat.completions.create.side_effect = socket.timeout("Request timeout")
    
    service = CorrectionService(api_key="test_key")
    
    result = service.correct(
        transcript_text="テスト",
        language="ja"
    )
    
    assert result['success'] is False
    assert 'error' in result


def test_split_long_text():
    """Test splitting long text for token limit handling"""
    from services.correction_service import CorrectionService
    
    service = CorrectionService(api_key="test_key")
    
    # Create long text (simulate >4000 tokens)
    long_text = "これはテストです。" * 1000
    
    chunks = service._split_text(long_text, max_tokens=1000)
    
    assert chunks is not None
    assert len(chunks) > 0


@patch('services.correction_service.OpenAI')
def test_correct_long_text_in_chunks(mock_openai_class):
    """Test correcting long text by splitting into chunks"""
    from services.correction_service import CorrectionService
    
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    # Mock response for each chunk
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "校正済み"
    mock_response.choices = [MagicMock(message=mock_message)]
    mock_client.chat.completions.create.return_value = mock_response
    
    service = CorrectionService(api_key="test_key")
    
    # Very long text
    long_text = "これはテストです。" * 500
    
    result = service.correct(transcript_text=long_text, language="ja")
    
    # Should handle long text
    assert result['success'] is True


def test_correction_result_structure():
    """Test that CorrectionResult has expected structure"""
    from services.correction_service import CorrectionResult
    
    result = CorrectionResult(
        success=True,
        corrected_text="校正後",
        original_text="校正前",
        changes_summary="誤字を修正",
        model="gpt-4o-mini"
    )
    
    assert result.success is True
    assert result.corrected_text == "校正後"
    assert result.original_text == "校正前"
    assert result.changes_summary == "誤字を修正"
    assert result.model == "gpt-4o-mini"


def test_logging_configuration():
    """Verify logging is configured for correction service"""
    import services.correction_service as correction_module
    
    assert hasattr(correction_module, 'logger')
