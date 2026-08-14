"""Unit test fixtures and configuration.

Shared fixtures are in tests/conftest.py — available to all test types,
including project_root, used by the fixtures below.
"""

import pytest


@pytest.fixture
def github_dir(project_root):
    """Return the .github directory."""
    return project_root / ".github"


@pytest.fixture
def workflows_dir(github_dir):
    """Return the workflows directory."""
    return github_dir / "workflows"


@pytest.fixture
def workflow_files(workflows_dir):
    """Return all workflow files."""
    return list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
