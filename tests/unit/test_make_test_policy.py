import pytest
from pathlib import Path


class TestMakeTestPolicy:
    """Tests for make test-policy target."""

    @pytest.fixture
    def makefile(self):
        return Path(__file__).parent.parent.parent / "Makefile"

    def test_makefile_has_test_policy_target(self, makefile):
        """Makefile must have a test-policy target."""
        content = makefile.read_text(encoding="utf-8")

        assert "test-policy:" in content

    def test_test_policy_target_uses_conftest(self, makefile):
        """test-policy target must invoke conftest."""
        content = makefile.read_text(encoding="utf-8")

        # Find the test-policy target and check its commands
        in_target = False
        target_commands = []
        for line in content.split("\n"):
            if line.startswith("test-policy:"):
                in_target = True
                continue
            if in_target and line.strip():
                if line.startswith("\t"):
                    target_commands.append(line.strip())
                else:
                    break

        assert any("conftest" in cmd for cmd in target_commands), (
            f"test-policy target must invoke conftest. Found: {target_commands}"
        )

    def test_test_policy_target_runs_valid_policy_files(self, makefile):
        """test-policy must validate compose.yaml, compose.suite.yaml, and .woodpecker.yml."""
        content = makefile.read_text(encoding="utf-8")

        # Find the test-policy target and check its commands
        in_target = False
        target_commands = []
        for line in content.split("\n"):
            if line.startswith("test-policy:"):
                in_target = True
                continue
            if in_target and line.strip():
                if line.startswith("\t"):
                    target_commands.append(line.strip())
                else:
                    break

        full_command = " ".join(target_commands)
        assert "compose.yaml" in full_command or "compose.suite.yaml" in full_command, (
            f"test-policy must validate compose files. Found: {full_command}"
        )
        assert ".woodpecker.yml" in full_command, (
            f"test-policy must validate .woodpecker.yml. Found: {full_command}"
        )
