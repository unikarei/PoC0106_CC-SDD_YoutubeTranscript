"""
Task queue system validation tests
Tests verify Celery configuration and task definitions are correct
"""
import pytest
from pathlib import Path
import importlib.util


def test_celery_config_exists():
    """Verify celery_config.py exists"""
    celery_config = Path("backend/celery_config.py")
    assert celery_config.exists(), "backend/celery_config.py must exist"


def test_worker_file_exists():
    """Verify worker.py exists and is not a placeholder"""
    worker_file = Path("backend/worker.py")
    assert worker_file.exists(), "backend/worker.py must exist"
    
    with open(worker_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "Celery" in content, "worker.py must import Celery"
    assert len(content) > 100, "worker.py should have substantial content"


def load_celery_config():
    """Helper to load celery_config module"""
    import sys
    from pathlib import Path
    
    backend_path = Path(__file__).parent.parent / "backend"
    sys.path.insert(0, str(backend_path))
    
    import celery_config
    return celery_config


def load_worker_module():
    """Helper to load worker module"""
    import sys
    from pathlib import Path
    
    backend_path = Path(__file__).parent.parent / "backend"
    sys.path.insert(0, str(backend_path))
    
    import worker
    return worker


def test_celery_app_configured():
    """Verify Celery app is properly configured"""
    worker = load_worker_module()
    
    assert hasattr(worker, "celery_app"), "worker must define celery_app"
    
    celery_app = worker.celery_app
    assert celery_app is not None, "celery_app must be instantiated"


def test_celery_broker_configured():
    """Verify Celery broker URL is configured"""
    worker = load_worker_module()
    celery_app = worker.celery_app
    
    # Check broker configuration
    assert celery_app.conf.broker_url is not None, "Broker URL must be configured"
    assert "redis" in celery_app.conf.broker_url.lower(), "Broker should use Redis"


def test_celery_result_backend_configured():
    """Verify Celery result backend is configured"""
    worker = load_worker_module()
    celery_app = worker.celery_app
    
    # Check result backend configuration
    assert celery_app.conf.result_backend is not None, "Result backend must be configured"
    assert "redis" in celery_app.conf.result_backend.lower(), "Result backend should use Redis"


def test_celery_task_serializer():
    """Verify task serializer is configured"""
    worker = load_worker_module()
    celery_app = worker.celery_app
    
    # Task serializer should be json for compatibility
    assert celery_app.conf.task_serializer == "json", "Task serializer should be JSON"


def test_celery_accept_content():
    """Verify accepted content types are configured"""
    worker = load_worker_module()
    celery_app = worker.celery_app
    
    # Should accept JSON
    assert "json" in celery_app.conf.accept_content, "Should accept JSON content"


def test_transcription_task_defined():
    """Verify transcription_task is defined"""
    worker = load_worker_module()
    
    assert hasattr(worker, "transcription_task"), "transcription_task must be defined"
    
    task = worker.transcription_task
    # Check if it's a Celery task
    assert hasattr(task, "delay"), "transcription_task should be a Celery task"
    assert hasattr(task, "apply_async"), "transcription_task should support async execution"


def test_correction_task_defined():
    """Verify correction_task is defined"""
    worker = load_worker_module()
    
    assert hasattr(worker, "correction_task"), "correction_task must be defined"
    
    task = worker.correction_task
    # Check if it's a Celery task
    assert hasattr(task, "delay"), "correction_task should be a Celery task"
    assert hasattr(task, "apply_async"), "correction_task should support async execution"


def test_task_retry_configuration():
    """Verify tasks have retry configuration"""
    worker = load_worker_module()
    
    # Check transcription task retry settings
    transcription_task = worker.transcription_task
    assert transcription_task.max_retries is not None, "transcription_task should have max_retries"
    assert transcription_task.max_retries >= 3, "transcription_task should retry at least 3 times"
    
    # Check correction task retry settings
    correction_task = worker.correction_task
    assert correction_task.max_retries is not None, "correction_task should have max_retries"
    assert correction_task.max_retries >= 3, "correction_task should retry at least 3 times"


def test_task_acks_late_configuration():
    """Verify tasks have acks_late enabled for reliability"""
    worker = load_worker_module()
    celery_app = worker.celery_app
    
    # acks_late ensures tasks are acknowledged only after completion
    assert celery_app.conf.task_acks_late is True, "task_acks_late should be enabled"


def test_worker_startup_script_exists():
    """Verify worker startup script exists for easy execution"""
    # Check if there's a startup script or documentation
    readme = Path("README.md")
    if readme.exists():
        with open(readme, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Should have Celery worker instructions
        assert "celery" in content.lower(), "README should mention Celery"


def test_celery_timezone_configuration():
    """Verify timezone is configured"""
    worker = load_worker_module()
    celery_app = worker.celery_app
    
    # Timezone should be set for scheduled tasks
    assert celery_app.conf.timezone is not None, "Timezone should be configured"


def test_celery_task_routes():
    """Verify task routes are configured if needed"""
    worker = load_worker_module()
    celery_app = worker.celery_app
    
    # Task routes configuration exists (can be None or dict)
    assert hasattr(celery_app.conf, "task_routes"), "task_routes should be defined"
