"""Shared test fixtures for uFawkesPipe unit tests."""

import pytest
import yaml
from pathlib import Path


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def docker_compose_file(project_root):
    """Return the docker-compose.yml file path (deprecated - use compose_file)."""
    return project_root / "docker-compose.yml"


@pytest.fixture
def docker_compose_config(docker_compose_file):
    """Load and return the docker-compose.yml configuration (deprecated - use compose_config)."""
    with open(docker_compose_file) as f:
        return yaml.safe_load(f)


@pytest.fixture
def compose_file(project_root):
    """Return the compose.yaml file path."""
    return project_root / "compose.yaml"


@pytest.fixture
def compose_config(compose_file):
    """Load and return the compose.yaml configuration."""
    with open(compose_file) as f:
        return yaml.safe_load(f)


@pytest.fixture
def woodpecker_file(project_root):
    """Return the .woodpecker.yml file path."""
    return project_root / ".woodpecker.yml"


@pytest.fixture
def woodpecker_config(woodpecker_file):
    """Load and return the .woodpecker.yml configuration."""
    with open(woodpecker_file) as f:
        return yaml.safe_load(f)


@pytest.fixture
def fawkespipe_example(project_root):
    """Return the .fawkespipe.yml.example file path."""
    return project_root / ".fawkespipe.yml.example"


@pytest.fixture
def fawkespipe_config(fawkespipe_example):
    """Load and return the .fawkespipe.yml.example configuration."""
    with open(fawkespipe_example) as f:
        return yaml.safe_load(f)
