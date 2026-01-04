"""
Tests for the update job title API endpoint
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime


# Test the API endpoint
class TestUpdateTitleAPI:
    """Test PATCH /api/jobs/{job_id}/title endpoint"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return MagicMock()

    @pytest.fixture
    def client(self):
        """Create test client"""
        from backend.main import app
        return TestClient(app)

    def test_update_title_success(self, client, mock_db):
        """Test successful title update"""
        job_id = "test-job-123"
        new_title = "Updated Title"
        
        # Mock the JobManager
        with patch('backend.routers.jobs.JobManager') as MockJobManager:
            mock_manager = MagicMock()
            MockJobManager.return_value = mock_manager
            
            # Mock get_job to return a job
            mock_job = MagicMock()
            mock_job.id = job_id
            mock_manager.get_job.return_value = mock_job
            
            # Mock update_job_title to succeed
            mock_manager.update_job_title.return_value = True
            
            response = client.patch(
                f"/api/jobs/{job_id}/title",
                json={"title": new_title}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == job_id
            assert data["title"] == new_title
            assert "message" in data

    def test_update_title_job_not_found(self, client, mock_db):
        """Test update title for non-existent job"""
        job_id = "non-existent-job"
        
        with patch('backend.routers.jobs.JobManager') as MockJobManager:
            mock_manager = MagicMock()
            MockJobManager.return_value = mock_manager
            mock_manager.get_job.return_value = None
            
            response = client.patch(
                f"/api/jobs/{job_id}/title",
                json={"title": "New Title"}
            )
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    def test_update_title_empty_title(self, client, mock_db):
        """Test update with empty title fails validation"""
        job_id = "test-job-123"
        
        response = client.patch(
            f"/api/jobs/{job_id}/title",
            json={"title": ""}
        )
        
        assert response.status_code == 422  # Validation error

    def test_update_title_too_long(self, client, mock_db):
        """Test update with title exceeding max length"""
        job_id = "test-job-123"
        long_title = "x" * 501  # Exceeds 500 char limit
        
        response = client.patch(
            f"/api/jobs/{job_id}/title",
            json={"title": long_title}
        )
        
        assert response.status_code == 422  # Validation error

    def test_update_title_whitespace_only(self, client, mock_db):
        """Test update with whitespace-only title fails"""
        job_id = "test-job-123"
        
        response = client.patch(
            f"/api/jobs/{job_id}/title",
            json={"title": "   "}
        )
        
        # Should fail validation (min_length after strip)
        assert response.status_code == 422


class TestJobManagerUpdateTitle:
    """Test JobManager.update_job_title method"""

    def test_update_job_title_success(self):
        """Test successful title update in job manager"""
        from backend.services.job_manager import JobManager
        from backend.models import Job, Item
        
        mock_db = MagicMock()
        
        # Create mock job and item
        mock_job = MagicMock(spec=Job)
        mock_job.id = "test-job-123"
        mock_job.user_title = "Old Title"
        
        mock_item = MagicMock(spec=Item)
        mock_item.title = "Old Title"
        
        # Setup query returns
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_job, mock_item]
        
        manager = JobManager(mock_db)
        result = manager.update_job_title("test-job-123", "New Title")
        
        assert result is True
        assert mock_job.user_title == "New Title"
        assert mock_item.title == "New Title"
        mock_db.commit.assert_called_once()

    def test_update_job_title_job_not_found(self):
        """Test update title when job doesn't exist"""
        from backend.services.job_manager import JobManager
        
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        manager = JobManager(mock_db)
        result = manager.update_job_title("non-existent", "New Title")
        
        assert result is False
        mock_db.commit.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
