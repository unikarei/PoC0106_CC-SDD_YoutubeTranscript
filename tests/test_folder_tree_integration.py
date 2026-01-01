"""
Integration tests for Folder Tree Library feature

Tests the basic functionality of folders, items, and tags
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base, get_db
from backend.main import app


# Test database URL (use a test database)
TEST_DATABASE_URL = "sqlite:///./test_folder_tree.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def test_client():
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)
    yield client
    Base.metadata.drop_all(bind=engine)


def test_get_folder_tree_empty(test_client):
    """Test getting folder tree when no folders exist"""
    response = test_client.get("/api/folders/tree")
    assert response.status_code == 200
    data = response.json()
    assert "folders" in data
    assert isinstance(data["folders"], list)


def test_create_folder(test_client):
    """Test creating a new folder"""
    response = test_client.post(
        "/api/folders/",
        json={
            "name": "Test Folder",
            "description": "A test folder",
            "icon": "📁"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Folder"
    assert data["description"] == "A test folder"
    assert data["icon"] == "📁"
    assert "id" in data
    return data["id"]


def test_create_subfolder(test_client):
    """Test creating a subfolder"""
    # First create parent
    parent_response = test_client.post(
        "/api/folders/",
        json={"name": "Parent Folder", "icon": "📂"}
    )
    assert parent_response.status_code == 201
    parent_id = parent_response.json()["id"]
    
    # Create child
    child_response = test_client.post(
        "/api/folders/",
        json={
            "name": "Child Folder",
            "parent_id": parent_id,
            "icon": "📄"
        }
    )
    assert child_response.status_code == 201
    child_data = child_response.json()
    assert child_data["name"] == "Child Folder"
    assert child_data["parent_id"] == parent_id
    assert "/Parent Folder/Child Folder" in child_data["path"]


def test_get_folder_tree_with_folders(test_client):
    """Test getting folder tree with folders"""
    response = test_client.get("/api/folders/tree")
    assert response.status_code == 200
    data = response.json()
    assert len(data["folders"]) > 0
    
    # Check folder structure
    folder = data["folders"][0]
    assert "id" in folder
    assert "name" in folder
    assert "item_count" in folder
    assert "children" in folder


def test_create_tag(test_client):
    """Test creating a tag"""
    response = test_client.post(
        "/api/tags/",
        json={"name": "test-tag", "color": "#FF0000"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-tag"
    assert data["color"] == "#FF0000"
    assert "id" in data
    return data["id"]


def test_get_tags(test_client):
    """Test getting all tags"""
    response = test_client.get("/api/tags/")
    assert response.status_code == 200
    data = response.json()
    assert "tags" in data
    assert isinstance(data["tags"], list)


def test_folder_settings(test_client):
    """Test folder settings"""
    # Create folder
    folder_response = test_client.post(
        "/api/folders/",
        json={"name": "Settings Test Folder"}
    )
    folder_id = folder_response.json()["id"]
    
    # Update settings
    settings_response = test_client.put(
        f"/api/folders/{folder_id}/settings",
        json={
            "default_language": "ja",
            "default_model": "gpt-4o-mini-transcribe",
            "default_qa_enabled": True
        }
    )
    assert settings_response.status_code == 200
    settings_data = settings_response.json()
    assert settings_data["default_language"] == "ja"
    assert settings_data["default_model"] == "gpt-4o-mini-transcribe"
    assert settings_data["default_qa_enabled"] is True
    
    # Get settings
    get_settings_response = test_client.get(f"/api/folders/{folder_id}/settings")
    assert get_settings_response.status_code == 200
    get_data = get_settings_response.json()
    assert get_data["default_language"] == "ja"


def test_delete_empty_folder(test_client):
    """Test deleting an empty folder"""
    # Create folder
    folder_response = test_client.post(
        "/api/folders/",
        json={"name": "Delete Test Folder"}
    )
    folder_id = folder_response.json()["id"]
    
    # Delete folder
    delete_response = test_client.delete(f"/api/folders/{folder_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True
    
    # Verify deleted
    get_response = test_client.get(f"/api/folders/{folder_id}")
    assert get_response.status_code == 404


def test_delete_tag(test_client):
    """Test deleting a tag"""
    # Create tag
    tag_response = test_client.post(
        "/api/tags/",
        json={"name": "delete-test-tag"}
    )
    tag_id = tag_response.json()["id"]
    
    # Delete tag
    delete_response = test_client.delete(f"/api/tags/{tag_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
