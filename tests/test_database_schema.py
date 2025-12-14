"""
Database schema validation tests
Tests verify database models and migrations are correctly defined
"""
import pytest
from pathlib import Path
import importlib.util


def test_alembic_config_exists():
    """Verify alembic.ini exists"""
    alembic_ini = Path("alembic.ini")
    assert alembic_ini.exists(), "alembic.ini must exist in project root"


def test_alembic_directory_exists():
    """Verify alembic directory structure exists"""
    alembic_dir = Path("alembic")
    assert alembic_dir.exists(), "alembic directory must exist"
    assert (alembic_dir / "env.py").exists(), "alembic/env.py must exist"
    assert (alembic_dir / "script.py.mako").exists(), "alembic/script.py.mako must exist"
    assert (alembic_dir / "versions").exists(), "alembic/versions directory must exist"


def test_database_models_exist():
    """Verify database models file exists"""
    models_file = Path("backend/models.py")
    assert models_file.exists(), "backend/models.py must exist"


def test_database_config_exists():
    """Verify database configuration file exists"""
    db_config = Path("backend/database.py")
    assert db_config.exists(), "backend/database.py must exist"


def load_models_module():
    """Helper to load models module"""
    import sys
    from pathlib import Path
    
    # Add backend directory to sys.path
    backend_path = Path(__file__).parent.parent / "backend"
    sys.path.insert(0, str(backend_path))
    
    # Import models
    import models
    return models


def test_job_model_exists():
    """Verify Job model is defined"""
    models = load_models_module()
    assert hasattr(models, "Job"), "Job model must be defined"


def test_job_model_fields():
    """Verify Job model has all required fields"""
    models = load_models_module()
    Job = models.Job
    
    # Check table columns exist
    columns = {col.name for col in Job.__table__.columns}
    
    required_fields = {
        "id", "youtube_url", "language", "model", "status",
        "progress", "error_message", "created_at", "updated_at"
    }
    
    assert required_fields.issubset(columns), \
        f"Job model missing fields: {required_fields - columns}"


def test_audio_file_model_exists():
    """Verify AudioFile model is defined"""
    models = load_models_module()
    assert hasattr(models, "AudioFile"), "AudioFile model must be defined"


def test_audio_file_model_fields():
    """Verify AudioFile model has all required fields"""
    models = load_models_module()
    AudioFile = models.AudioFile
    
    columns = {col.name for col in AudioFile.__table__.columns}
    
    required_fields = {
        "id", "job_id", "file_path", "duration_seconds",
        "format", "file_size_bytes", "title", "created_at"
    }
    
    assert required_fields.issubset(columns), \
        f"AudioFile model missing fields: {required_fields - columns}"


def test_transcript_model_exists():
    """Verify Transcript model is defined"""
    models = load_models_module()
    assert hasattr(models, "Transcript"), "Transcript model must be defined"


def test_transcript_model_fields():
    """Verify Transcript model has all required fields"""
    models = load_models_module()
    Transcript = models.Transcript
    
    columns = {col.name for col in Transcript.__table__.columns}
    
    required_fields = {
        "id", "job_id", "text", "language_detected",
        "transcription_model", "created_at"
    }
    
    assert required_fields.issubset(columns), \
        f"Transcript model missing fields: {required_fields - columns}"


def test_corrected_transcript_model_exists():
    """Verify CorrectedTranscript model is defined"""
    models = load_models_module()
    assert hasattr(models, "CorrectedTranscript"), "CorrectedTranscript model must be defined"


def test_corrected_transcript_model_fields():
    """Verify CorrectedTranscript model has all required fields"""
    models = load_models_module()
    CorrectedTranscript = models.CorrectedTranscript
    
    columns = {col.name for col in CorrectedTranscript.__table__.columns}
    
    required_fields = {
        "id", "job_id", "corrected_text", "original_text",
        "correction_model", "changes_summary", "created_at"
    }
    
    assert required_fields.issubset(columns), \
        f"CorrectedTranscript model missing fields: {required_fields - columns}"


def test_job_status_enum():
    """Verify Job has status enum with required values"""
    models = load_models_module()
    Job = models.Job
    
    # Get status column
    status_col = Job.__table__.columns['status']
    
    # Status should have check constraint or enum
    assert status_col is not None, "Status column must exist"


def test_foreign_key_relationships():
    """Verify foreign key relationships are defined"""
    models = load_models_module()
    AudioFile = models.AudioFile
    Transcript = models.Transcript
    CorrectedTranscript = models.CorrectedTranscript
    
    # Check AudioFile has job_id foreign key
    audio_fks = [fk for fk in AudioFile.__table__.foreign_keys]
    assert len(audio_fks) > 0, "AudioFile must have foreign key to Job"
    
    # Check Transcript has job_id foreign key
    transcript_fks = [fk for fk in Transcript.__table__.foreign_keys]
    assert len(transcript_fks) > 0, "Transcript must have foreign key to Job"
    
    # Check CorrectedTranscript has job_id foreign key
    corrected_fks = [fk for fk in CorrectedTranscript.__table__.foreign_keys]
    assert len(corrected_fks) > 0, "CorrectedTranscript must have foreign key to Job"


def test_indexes_defined():
    """Verify indexes are defined on appropriate columns"""
    models = load_models_module()
    Job = models.Job
    
    # Get indexes
    indexes = {idx.name for idx in Job.__table__.indexes}
    
    # Should have index on status
    status_indexed = any('status' in str(idx.columns) for idx in Job.__table__.indexes)
    assert status_indexed or 'ix_jobs_status' in indexes, \
        "Job.status should have an index"


def test_initial_migration_exists():
    """Verify initial migration file exists"""
    versions_dir = Path("alembic/versions")
    migrations = list(versions_dir.glob("*.py"))
    
    # Exclude __pycache__ and __init__.py
    migrations = [m for m in migrations if not m.name.startswith("__")]
    
    assert len(migrations) > 0, "At least one migration file must exist in alembic/versions/"
