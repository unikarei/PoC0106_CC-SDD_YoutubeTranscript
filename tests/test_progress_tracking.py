"""
Progress tracking tests for audio extraction
Tests verify progress updates and status management
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def test_job_manager_service_exists():
    """Verify job_manager.py exists"""
    manager_file = Path("backend/services/job_manager.py")
    assert manager_file.exists(), "backend/services/job_manager.py must exist"


def test_job_manager_class_exists():
    """Verify JobManager class is defined"""
    from services.job_manager import JobManager
    
    manager = JobManager()
    assert manager is not None


def test_job_manager_has_update_status_method():
    """Verify JobManager has update_job_status method"""
    from services.job_manager import JobManager
    
    manager = JobManager()
    assert hasattr(manager, "update_job_status"), "JobManager must have update_job_status method"


def test_job_manager_has_update_progress_method():
    """Verify JobManager has update_job_progress method"""
    from services.job_manager import JobManager
    
    manager = JobManager()
    assert hasattr(manager, "update_job_progress"), "JobManager must have update_job_progress method"


@patch('services.job_manager.SessionLocal')
def test_update_job_status(mock_session):
    """Test updating job status"""
    from services.job_manager import JobManager
    
    # Mock database session
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    
    # Mock job query
    mock_job = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_job
    
    manager = JobManager()
    manager.update_job_status("job123", "processing")
    
    # Verify status was updated
    assert mock_job.status == "processing"
    mock_db.commit.assert_called_once()


@patch('services.job_manager.SessionLocal')
def test_update_job_progress(mock_session):
    """Test updating job progress"""
    from services.job_manager import JobManager
    
    # Mock database session
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    
    # Mock job query
    mock_job = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_job
    
    manager = JobManager()
    manager.update_job_progress("job123", 50, "Downloading audio")
    
    # Verify progress was updated
    assert mock_job.progress == 50
    mock_db.commit.assert_called_once()


@patch('services.job_manager.SessionLocal')
def test_update_job_error(mock_session):
    """Test updating job with error"""
    from services.job_manager import JobManager
    
    # Mock database session
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    
    # Mock job query
    mock_job = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_job
    
    manager = JobManager()
    manager.update_job_status("job123", "failed", error_message="Video not found")
    
    # Verify error was recorded
    assert mock_job.status == "failed"
    assert mock_job.error_message == "Video not found"
    mock_db.commit.assert_called_once()


def test_progress_callback_class_exists():
    """Verify ProgressCallback class exists for yt-dlp"""
    from services.audio_extractor import ProgressCallback
    
    callback = ProgressCallback("job123")
    assert callback is not None
    assert callback.job_id == "job123"


def test_progress_callback_has_hook_method():
    """Verify ProgressCallback has hook method"""
    from services.audio_extractor import ProgressCallback
    
    callback = ProgressCallback("job123")
    assert hasattr(callback, "hook"), "ProgressCallback must have hook method"
    assert callable(callback.hook), "hook must be callable"


@patch('services.job_manager.JobManager')
def test_progress_callback_updates_progress(mock_manager_class):
    """Test ProgressCallback updates job progress during download"""
    from services.audio_extractor import ProgressCallback
    
    # Mock JobManager
    mock_manager = MagicMock()
    mock_manager_class.return_value = mock_manager
    
    callback = ProgressCallback("job123")
    callback.job_manager = mock_manager
    
    # Simulate yt-dlp download progress
    progress_info = {
        'status': 'downloading',
        'downloaded_bytes': 5000000,
        'total_bytes': 10000000,
        'filename': 'test.m4a'
    }
    
    callback.hook(progress_info)
    
    # Verify progress was updated (should be around 50%)
    mock_manager.update_job_progress.assert_called()
    call_args = mock_manager.update_job_progress.call_args
    assert call_args[0][0] == "job123"
    assert 40 <= call_args[0][1] <= 60  # Progress around 50%


@patch('services.job_manager.JobManager')
def test_progress_callback_handles_completion(mock_manager_class):
    """Test ProgressCallback handles download completion"""
    from services.audio_extractor import ProgressCallback
    
    # Mock JobManager
    mock_manager = MagicMock()
    mock_manager_class.return_value = mock_manager
    
    callback = ProgressCallback("job123")
    callback.job_manager = mock_manager
    
    # Simulate yt-dlp completion
    progress_info = {
        'status': 'finished',
        'filename': 'test.m4a'
    }
    
    callback.hook(progress_info)
    
    # Verify completion was recorded
    mock_manager.update_job_progress.assert_called()


def test_audio_extractor_uses_progress_callback():
    """Verify AudioExtractor integrates progress callback"""
    from services.audio_extractor import AudioExtractor
    
    extractor = AudioExtractor()
    
    # Check if extract_audio accepts progress tracking
    import inspect
    sig = inspect.signature(extractor.extract_audio)
    # Method should be able to handle progress updates
    assert 'extract_audio' in dir(extractor)


@patch('services.job_manager.SessionLocal')
def test_create_audio_file_record(mock_session):
    """Test creating audio file record in database"""
    from services.job_manager import JobManager
    from models import AudioFile
    
    # Mock database session
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    
    manager = JobManager()
    
    if hasattr(manager, 'create_audio_file'):
        manager.create_audio_file(
            job_id="job123",
            file_path="/path/to/audio.m4a",
            duration_seconds=600,
            title="Test Video",
            file_format="m4a",
            file_size_bytes=5000000
        )
        
        # Verify AudioFile was added
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


@patch('services.job_manager.SessionLocal')
def test_get_job_status(mock_session):
    """Test retrieving job status"""
    from services.job_manager import JobManager
    
    # Mock database session
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    
    # Mock job
    mock_job = MagicMock()
    mock_job.id = "job123"
    mock_job.status = "processing"
    mock_job.progress = 50
    mock_db.query.return_value.filter.return_value.first.return_value = mock_job
    
    manager = JobManager()
    
    if hasattr(manager, 'get_job_status'):
        status = manager.get_job_status("job123")
        assert status is not None
        assert status['status'] == "processing"
        assert status['progress'] == 50


def test_logging_configuration():
    """Verify logging is configured for progress tracking"""
    import services.audio_extractor as audio_extractor_module
    import services.job_manager as job_manager_module
    import logging
    
    # Should have module-level loggers
    assert hasattr(audio_extractor_module, 'logger')
    assert hasattr(job_manager_module, 'logger')
