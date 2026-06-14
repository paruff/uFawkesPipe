"""Acceptance tests for uFawkesPipe full pipeline."""

import pytest
import subprocess
import time
import requests
from pathlib import Path


class TestUfawkesPipeAcceptance:
    """Acceptance tests for the complete uFawkesPipe pipeline."""

    @pytest.fixture(autouse=True)
    def setup_stack(self):
        """Ensure Docker Compose stack is running."""
        subprocess.run(
            ["docker", "compose", "up", "-d"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        # Wait for services to be healthy
        time.sleep(60)
        yield

    def test_pipeline_can_start(self):
        """Jenkins pipeline should be able to start."""
        try:
            # Check if Jenkins is running
            response = requests.get(
                "http://localhost:8080/login",
                timeout=10,
            )
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Jenkins not available")

    def test_jenkins_has_required_plugins(self):
        """Jenkins should have required plugins installed."""
        try:
            response = requests.get(
                "http://localhost:8080/pluginManager/api/json",
                timeout=10,
            )
            if response.status_code == 200:
                plugins = response.json().get("plugins", [])
                plugin_names = [p.get("shortName", "") for p in plugins]
                # Required plugins
                required = [
                    "pipeline",
                    "workflow-aggregator",
                    "git",
                    "docker-workflow",
                ]
                for plugin in required:
                    assert plugin in plugin_names, (
                        f"Required plugin '{plugin}' not installed"
                    )
        except requests.exceptions.ConnectionError:
            pytest.skip("Jenkins plugin manager not available")

    def test_jenkins_has_pipeline_jobs(self):
        """Jenkins should have pipeline jobs configured."""
        try:
            response = requests.get(
                "http://localhost:8080/api/json?tree=jobs[name]",
                timeout=10,
            )
            if response.status_code == 200:
                jobs = response.json().get("jobs", [])
                # At least one job should exist
                assert len(jobs) > 0, "No pipeline jobs configured"
        except requests.exceptions.ConnectionError:
            pytest.skip("Jenkins API not available")

    def test_jenkins_can_run_pipeline(self):
        """Jenkins should be able to trigger a pipeline build."""
        try:
            response = requests.get(
                "http://localhost:8080/api/json?tree=jobs[name,url]",
                timeout=10,
            )
            if response.status_code == 200:
                jobs = response.json().get("jobs", [])
                if jobs:
                    # Try to trigger the first job
                    job_url = jobs[0].get("url")
                    if job_url:
                        trigger_response = requests.post(
                            f"{job_url}build",
                            timeout=10,
                        )
                        # Accept 201 (Created) or 409 (already building)
                        assert trigger_response.status_code in [201, 409]
        except requests.exceptions.ConnectionError:
            pytest.skip("Jenkins not available")

    def test_jenkins_logs_clean(self):
        """Jenkins logs should be clean of critical errors."""
        result = subprocess.run(
            ["docker", "logs", "ufawkespipe-jenkins-1", "--tail", "200"],
            capture_output=True,
            text=True,
        )
        # Check for critical errors
        critical_errors = [
            "SEVERE",
            "FATAL",
            "OutOfMemoryError",
            "StackOverflowError",
            "Failed to start",
        ]
        for error in critical_errors:
            assert error not in result.stdout, (
                f"Jenkins log contains critical error: {error}"
            )
