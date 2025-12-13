"""
Tests for ExportService
Handles exporting transcripts to various formats (TXT, SRT, VTT)
"""
import pytest
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def test_export_service_exists():
    """Verify ExportService module exists"""
    from services import export_service
    assert export_service is not None


def test_export_service_class_exists():
    """Verify ExportService class is defined"""
    from services.export_service import ExportService
    assert ExportService is not None


def test_export_service_initialization():
    """Test ExportService can be initialized"""
    from services.export_service import ExportService
    
    service = ExportService()
    assert service is not None


def test_export_to_txt():
    """Test exporting transcript to plain text format"""
    from services.export_service import ExportService
    
    service = ExportService()
    
    transcript = "これはテストの文字起こしです。\n\n二つ目の段落です。"
    
    result = service.export_to_txt(transcript)
    
    assert result is not None
    assert isinstance(result, str)
    assert "テスト" in result


def test_export_to_srt():
    """Test exporting transcript to SRT subtitle format"""
    from services.export_service import ExportService
    
    service = ExportService()
    
    transcript = "最初の文です。二つ目の文です。三つ目の文です。"
    duration_seconds = 30  # 30 seconds total
    
    result = service.export_to_srt(transcript, duration_seconds)
    
    assert result is not None
    assert isinstance(result, str)
    # SRT format: sequence number, timestamps, text
    assert "1" in result
    assert "00:00:00" in result
    assert "-->" in result


def test_export_to_vtt():
    """Test exporting transcript to WebVTT format"""
    from services.export_service import ExportService
    
    service = ExportService()
    
    transcript = "最初の文です。二つ目の文です。"
    duration_seconds = 20
    
    result = service.export_to_vtt(transcript, duration_seconds)
    
    assert result is not None
    assert isinstance(result, str)
    assert "WEBVTT" in result
    assert "00:00:00" in result


def test_srt_timestamp_format():
    """Test SRT timestamp formatting"""
    from services.export_service import ExportService
    
    service = ExportService()
    
    # Test specific timestamp
    timestamp = service._format_srt_timestamp(65.5)  # 1 minute 5.5 seconds
    
    assert timestamp is not None
    assert "00:01:05" in timestamp
    assert "," in timestamp  # SRT uses comma for milliseconds


def test_vtt_timestamp_format():
    """Test VTT timestamp formatting"""
    from services.export_service import ExportService
    
    service = ExportService()
    
    # Test specific timestamp
    timestamp = service._format_vtt_timestamp(125.750)  # 2 minutes 5.75 seconds
    
    assert timestamp is not None
    assert "00:02:05" in timestamp
    assert "." in timestamp  # VTT uses dot for milliseconds


def test_split_text_into_segments():
    """Test splitting text into timed segments"""
    from services.export_service import ExportService
    
    service = ExportService()
    
    transcript = "最初の文。二つ目の文。三つ目の文。"
    duration_seconds = 30
    
    segments = service._split_into_segments(transcript, duration_seconds)
    
    assert segments is not None
    assert len(segments) > 0
    assert all('text' in seg and 'start' in seg and 'end' in seg for seg in segments)


def test_distribute_timestamps_evenly():
    """Test even distribution of timestamps across segments"""
    from services.export_service import ExportService
    
    service = ExportService()
    
    # 3 sentences over 30 seconds = 10 seconds each
    segments = [
        {'text': '最初の文。'},
        {'text': '二つ目の文。'},
        {'text': '三つ目の文。'}
    ]
    
    result = service._distribute_timestamps(segments, 30)
    
    assert len(result) == 3
    assert result[0]['start'] == 0
    assert result[2]['end'] == 30


def test_export_with_empty_text():
    """Test exporting empty transcript"""
    from services.export_service import ExportService
    
    service = ExportService()
    
    result = service.export_to_txt("")
    
    # Should handle empty text gracefully
    assert result is not None


def test_export_with_very_long_text():
    """Test exporting very long transcript"""
    from services.export_service import ExportService
    
    service = ExportService()
    
    long_transcript = "これはテストです。" * 1000
    
    result = service.export_to_txt(long_transcript)
    
    assert result is not None
    assert len(result) > 0


def test_srt_sequence_numbers():
    """Test SRT format has correct sequence numbers"""
    from services.export_service import ExportService
    
    service = ExportService()
    
    transcript = "一つ目。二つ目。三つ目。"
    
    result = service.export_to_srt(transcript, 30)
    
    # Should have sequential numbers
    assert "1\n" in result
    assert "2\n" in result
    assert "3\n" in result


def test_validate_srt_format():
    """Test SRT format validation"""
    from services.export_service import ExportService
    
    service = ExportService()
    
    valid_srt = """1
00:00:00,000 --> 00:00:05,000
First subtitle

2
00:00:05,000 --> 00:00:10,000
Second subtitle
"""
    
    is_valid = service.validate_srt_format(valid_srt)
    
    assert is_valid is True


def test_validate_vtt_format():
    """Test VTT format validation"""
    from services.export_service import ExportService
    
    service = ExportService()
    
    valid_vtt = """WEBVTT

00:00:00.000 --> 00:00:05.000
First subtitle

00:00:05.000 --> 00:00:10.000
Second subtitle
"""
    
    is_valid = service.validate_vtt_format(valid_vtt)
    
    assert is_valid is True


def test_export_handles_special_characters():
    """Test exporting text with special characters"""
    from services.export_service import ExportService
    
    service = ExportService()
    
    transcript = "特殊文字: @#$%^&*() 日本語！？"
    
    result_txt = service.export_to_txt(transcript)
    result_srt = service.export_to_srt(transcript, 10)
    result_vtt = service.export_to_vtt(transcript, 10)
    
    # Should preserve special characters
    assert "特殊文字" in result_txt
    assert "@#$" in result_txt


def test_export_result_structure():
    """Test that ExportResult has expected structure"""
    from services.export_service import ExportResult
    
    result = ExportResult(
        success=True,
        format="txt",
        content="Sample text",
        filename="transcript.txt"
    )
    
    assert result.success is True
    assert result.format == "txt"
    assert result.content == "Sample text"
    assert result.filename == "transcript.txt"


def test_logging_configuration():
    """Verify logging is configured for export service"""
    import services.export_service as export_module
    
    assert hasattr(export_module, 'logger')
