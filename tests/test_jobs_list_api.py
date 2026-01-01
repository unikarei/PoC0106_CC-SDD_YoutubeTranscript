from pathlib import Path
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from database import Base, get_db
from models import Job, AudioFile, Transcript, CorrectedTranscript, QaResult
from routers import jobs as jobs_router


# Create a single engine and session maker for all tests
engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Create all tables once for all tests in this module"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    """Provide a database session for tests"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    """Provide a test client with seeded data"""
    def override_get_db():
        try:
            yield db
        finally:
            pass  # Don't close here, fixture handles it

    app = FastAPI()
    app.dependency_overrides[get_db] = override_get_db
    app.include_router(jobs_router.router, prefix="/api/jobs")

    # Seed one job
    job = Job(
        youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        language="en",
        model="gpt-4o-mini-transcribe",
        status="pending",
        progress=0,
        user_title="Test Title",
        tags="tag1;tag2",
    )
    db.add(job)
    db.commit()

    yield TestClient(app)

    # Cleanup after each test
    db.query(Job).delete()
    db.commit()


def test_list_jobs_returns_seeded_job(client: TestClient):
    r = client.get("/api/jobs/")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["youtube_url"].startswith("https://www.youtube.com/")


def test_list_jobs_filters_by_tag(client: TestClient):
    r = client.get("/api/jobs/?tag=tag1")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1

    r2 = client.get("/api/jobs/?tag=nonexistent")
    assert r2.status_code == 200
    assert r2.json()["total"] == 0
