"""
Infrastructure validation tests for Docker setup
Tests verify Docker Compose configuration is valid and services are defined correctly
"""
import yaml
import os
from pathlib import Path


def test_docker_compose_file_exists():
    """Verify docker-compose.yml exists in project root"""
    compose_file = Path("docker-compose.yml")
    assert compose_file.exists(), "docker-compose.yml must exist in project root"


def test_docker_compose_valid_yaml():
    """Verify docker-compose.yml is valid YAML"""
    with open("docker-compose.yml", "r") as f:
        config = yaml.safe_load(f)
    assert config is not None, "docker-compose.yml must be valid YAML"


def test_docker_compose_has_required_services():
    """Verify all required services are defined"""
    with open("docker-compose.yml", "r") as f:
        config = yaml.safe_load(f)
    
    services = config.get("services", {})
    required_services = ["api", "worker", "redis", "postgres"]
    
    for service in required_services:
        assert service in services, f"Service '{service}' must be defined in docker-compose.yml"


def test_docker_compose_postgres_config():
    """Verify PostgreSQL service configuration"""
    with open("docker-compose.yml", "r") as f:
        config = yaml.safe_load(f)
    
    postgres = config["services"]["postgres"]
    assert "image" in postgres, "PostgreSQL must have image specified"
    assert "postgres" in postgres["image"].lower(), "PostgreSQL image must be postgres"
    assert "environment" in postgres, "PostgreSQL must have environment variables"
    
    env = postgres["environment"]
    assert "POSTGRES_DB" in env, "PostgreSQL must have POSTGRES_DB"
    assert "POSTGRES_USER" in env, "PostgreSQL must have POSTGRES_USER"
    assert "POSTGRES_PASSWORD" in env, "PostgreSQL must have POSTGRES_PASSWORD"


def test_docker_compose_redis_config():
    """Verify Redis service configuration"""
    with open("docker-compose.yml", "r") as f:
        config = yaml.safe_load(f)
    
    redis = config["services"]["redis"]
    assert "image" in redis, "Redis must have image specified"
    assert "redis" in redis["image"].lower(), "Redis image must be redis"


def test_docker_compose_api_config():
    """Verify API service configuration"""
    with open("docker-compose.yml", "r") as f:
        config = yaml.safe_load(f)
    
    api = config["services"]["api"]
    assert "build" in api or "image" in api, "API must have build or image specified"
    assert "ports" in api, "API must expose ports"
    assert "depends_on" in api, "API must depend on other services"
    
    # API should depend on postgres and redis
    depends_on = api["depends_on"]
    assert "postgres" in depends_on, "API must depend on postgres"
    assert "redis" in depends_on, "API must depend on redis"


def test_docker_compose_worker_config():
    """Verify Worker service configuration"""
    with open("docker-compose.yml", "r") as f:
        config = yaml.safe_load(f)
    
    worker = config["services"]["worker"]
    assert "build" in worker or "image" in worker, "Worker must have build or image specified"
    assert "depends_on" in worker, "Worker must depend on other services"
    
    # Worker should depend on postgres and redis
    depends_on = worker["depends_on"]
    assert "postgres" in depends_on, "Worker must depend on postgres"
    assert "redis" in depends_on, "Worker must depend on redis"


def test_env_example_file_exists():
    """Verify .env.example exists"""
    env_example = Path(".env.example")
    assert env_example.exists(), ".env.example must exist in project root"


def test_env_example_has_required_vars():
    """Verify .env.example contains all required environment variables"""
    with open(".env.example", "r") as f:
        content = f.read()
    
    required_vars = [
        "OPENAI_API_KEY",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "REDIS_URL",
        "DATABASE_URL"
    ]
    
    for var in required_vars:
        assert var in content, f"Environment variable '{var}' must be in .env.example"


def test_dockerignore_exists():
    """Verify .dockerignore exists"""
    dockerignore = Path(".dockerignore")
    assert dockerignore.exists(), ".dockerignore must exist in project root"


def test_dockerignore_excludes_common_files():
    """Verify .dockerignore excludes common unnecessary files"""
    with open(".dockerignore", "r") as f:
        content = f.read()
    
    expected_patterns = [".env", ".git", "__pycache__", "*.pyc", ".venv"]
    
    for pattern in expected_patterns:
        assert pattern in content, f"Pattern '{pattern}' should be in .dockerignore"
