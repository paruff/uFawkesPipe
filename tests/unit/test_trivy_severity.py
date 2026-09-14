import pytest
from pathlib import Path


class TestTrivySeverityAlignment:
    """Tests for Trivy severity threshold alignment across config files."""

    @pytest.fixture
    def woodpecker_yml(self):
        return Path(__file__).parent.parent.parent / ".woodpecker.yml"

    @pytest.fixture
    def fawkespipe_example(self):
        return Path(__file__).parent.parent.parent / ".fawkespipe.yml.example"

    @pytest.fixture
    def pipeline_contract_doc(self):
        return Path(__file__).parent.parent.parent / "docs" / "pipeline-contract.md"

    def test_fawkespipe_example_trivy_severity(self, fawkespipe_example):
        """fawkespipe.yml.example must have trivy.severity = HIGH,CRITICAL."""
        with open(fawkespipe_example, encoding="utf-8") as f:
            content = f.read()

        assert (
            "severity: HIGH,CRITICAL" in content
            or "severity: HIGH, CRITICAL" in content
        )

    def test_woodpecker_trivy_fs_scan_severity(self, woodpecker_yml):
        """vuln-scan-fs step must filter HIGH,CRITICAL severity."""
        with open(woodpecker_yml, encoding="utf-8") as f:
            content = f.read()

        assert "--severity HIGH,CRITICAL" in content

    def test_pipeline_contract_doc_severity_matches(self, pipeline_contract_doc):
        """pipeline-contract.md trivy.severity default must match HIGH,CRITICAL."""
        with open(pipeline_contract_doc, encoding="utf-8") as f:
            content = f.read()

        assert "`HIGH,CRITICAL`" in content
