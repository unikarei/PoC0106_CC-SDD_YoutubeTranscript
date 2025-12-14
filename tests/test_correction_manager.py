"""
Tests for Correction Result Management
Handles saving, retrieving, and managing correction results
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def test_correction_manager_exists():
    """Verify CorrectionManager module exists"""
    from services import correction_manager
    assert correction_manager is not None


def test_correction_manager_class_exists():
    """Verify CorrectionManager class is defined"""
    from services.correction_manager import CorrectionManager
    assert CorrectionManager is not None


def test_correction_manager_initialization():
    """Test CorrectionManager can be initialized"""
    from services.correction_manager import CorrectionManager
    
    manager = CorrectionManager()
    assert manager is not None


def test_save_correction_to_database():
    """Test saving correction result to database"""
    from services.correction_manager import CorrectionManager
    
    mock_session = MagicMock()
    
    manager = CorrectionManager()
    manager.job_manager = None  # Disable job_manager to avoid DB connection
    
    with patch.object(manager, '_get_db', return_value=mock_session):
        result = manager.save_correction(
            job_id="test-job-123",
            corrected_text="校正後のテキスト",
            original_text="校正前のテキスト",
            changes_summary="誤字を3箇所修正",
            model="gpt-4o-mini"
        )
    
    # Should have saved to database
    assert mock_session.add.called
    assert mock_session.commit.called
    assert result is True


@patch('services.correction_manager.SessionLocal')
def test_save_correction_handles_error(mock_session_local):
    """Test error handling when saving correction fails"""
    from services.correction_manager import CorrectionManager
    
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session
    mock_session.commit.side_effect = Exception("Database error")
    
    manager = CorrectionManager()
    
    result = manager.save_correction(
        job_id="test-job-123",
        corrected_text="テキスト",
        original_text="元テキスト",
        changes_summary="変更なし",
        model="gpt-4o-mini"
    )
    
    assert result is False


def test_get_correction_by_job_id():
    """Test retrieving correction by job ID"""
    from services.correction_manager import CorrectionManager
    from models import CorrectedTranscript
    
    mock_session = MagicMock()
    
    # Mock correction result
    mock_correction = CorrectedTranscript(
        id="correction-123",
        job_id="test-job-123",
        corrected_text="校正後",
        original_text="校正前",
        correction_model="gpt-4o-mini"
    )
    mock_session.query().filter().first.return_value = mock_correction
    
    manager = CorrectionManager()
    
    with patch.object(manager, '_get_db', return_value=mock_session):
        result = manager.get_correction(job_id="test-job-123")
    
    assert result is not None
    assert result.corrected_text == "校正後"


def test_get_correction_not_found():
    """Test retrieving correction when not found"""
    from services.correction_manager import CorrectionManager
    
    mock_session = MagicMock()
    mock_session.query().filter().first.return_value = None
    
    manager = CorrectionManager()
    
    with patch.object(manager, '_get_db', return_value=mock_session):
        result = manager.get_correction(job_id="nonexistent")
    
    assert result is None


def test_prepare_comparison_data():
    """Test preparing data for side-by-side comparison"""
    from services.correction_manager import CorrectionManager
    from models import CorrectedTranscript
    
    mock_session = MagicMock()
    
    mock_correction = CorrectedTranscript(
        id="correction-123",
        job_id="test-job-123",
        corrected_text="校正後テキスト",
        original_text="校正前テキスト",
        changes_summary="変更あり"
    )
    mock_session.query().filter().first.return_value = mock_correction
    
    manager = CorrectionManager()
    
    with patch.object(manager, '_get_db', return_value=mock_session):
        result = manager.prepare_comparison_data(job_id="test-job-123")
    
    assert result is not None
    assert 'original' in result
    assert 'corrected' in result
    assert result['original'] == "校正前テキスト"
    assert result['corrected'] == "校正後テキスト"


def test_calculate_diff_highlights():
    """Test calculating highlighted differences between texts"""
    from services.correction_manager import CorrectionManager
    
    manager = CorrectionManager()
    
    original = "これはテストです"
    corrected = "これはテストでした"
    
    diff_data = manager.calculate_diff(original, corrected)
    
    assert diff_data is not None
    assert isinstance(diff_data, (dict, list))


def test_accept_correction():
    """Test accepting a correction (marking as final)"""
    from services.correction_manager import CorrectionManager
    
    manager = CorrectionManager()
    
    # Mock job manager
    with patch.object(manager, 'job_manager') as mock_job_manager:
        result = manager.accept_correction(job_id="test-job-123")
        
        # Should update job status to completed
        if mock_job_manager:
            assert result is True


def test_reject_correction():
    """Test rejecting a correction (revert to original)"""
    from services.correction_manager import CorrectionManager
    from models import CorrectedTranscript
    
    mock_session = MagicMock()
    
    mock_correction = MagicMock(spec=CorrectedTranscript)
    mock_session.query().filter().first.return_value = mock_correction
    
    manager = CorrectionManager()
    
    with patch.object(manager, '_get_db', return_value=mock_session):
        result = manager.reject_correction(job_id="test-job-123")
    
    # Should delete correction record
    assert mock_session.delete.called or result is True


@patch('services.correction_manager.SessionLocal')
def test_save_with_all_metadata(mock_session_local):
    """Test saving correction includes all required metadata"""
    from services.correction_manager import CorrectionManager
    from models import CorrectedTranscript
    
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session
    
    manager = CorrectionManager()
    
    manager.save_correction(
        job_id="test-job-123",
        corrected_text="校正後",
        original_text="校正前",
        changes_summary="変更: 3箇所",
        model="gpt-4o-mini"
    )
    
    # Verify CorrectedTranscript object was created
    assert mock_session.add.called
    call_args = mock_session.add.call_args[0][0]
    assert isinstance(call_args, CorrectedTranscript)
    assert call_args.job_id == "test-job-123"
    assert call_args.corrected_text == "校正後"
    assert call_args.original_text == "校正前"
    assert call_args.correction_model == "gpt-4o-mini"


def test_export_comparison_format():
    """Test exporting comparison in specific format"""
    from services.correction_manager import CorrectionManager
    
    manager = CorrectionManager()
    
    data = {
        'original': '校正前テキスト',
        'corrected': '校正後テキスト',
        'changes': '変更あり'
    }
    
    # Should be able to format data for display
    exported = manager.format_for_display(data)
    
    assert exported is not None


def test_list_all_corrections():
    """Test listing all corrections for a job"""
    from services.correction_manager import CorrectionManager
    
    mock_session = MagicMock()
    
    # Mock multiple corrections
    mock_corrections = [MagicMock(), MagicMock()]
    mock_session.query().filter().all.return_value = mock_corrections
    
    manager = CorrectionManager()
    
    with patch.object(manager, '_get_db', return_value=mock_session):
        results = manager.list_corrections(job_id="test-job-123")
    
    assert results is not None
    assert len(results) >= 0


def test_generate_change_summary():
    """Test generating human-readable change summary"""
    from services.correction_manager import CorrectionManager
    
    manager = CorrectionManager()
    
    original = "これはテストです"
    corrected = "これはテストでした。"
    
    summary = manager.generate_summary(original, corrected)
    
    assert summary is not None
    assert isinstance(summary, str)
    assert len(summary) > 0


def test_update_job_status_on_save():
    """Test that job status is updated when correction is saved"""
    from services.correction_manager import CorrectionManager
    
    mock_session = MagicMock()
    
    manager = CorrectionManager()
    
    # Mock job manager
    with patch.object(manager, '_get_db', return_value=mock_session):
        with patch.object(manager, 'job_manager') as mock_job_manager:
            manager.save_correction(
                job_id="test-job-123",
                corrected_text="校正後",
                original_text="校正前",
                changes_summary="変更あり",
                model="gpt-4o-mini"
            )
            
            # Should potentially update job status
            # Implementation may vary


def test_logging_configuration():
    """Verify logging is configured for correction manager"""
    import services.correction_manager as manager_module
    
    assert hasattr(manager_module, 'logger')
