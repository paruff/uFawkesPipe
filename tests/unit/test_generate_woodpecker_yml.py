"""Tests for scripts/generate_woodpecker_yml.py.

Encodes specification.md (PIPE-009) AC-01..AC-04 against the field -> step
mapping documented in design.md §5.
"""

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import generate_woodpecker_yml as gen  # noqa: E402


def _contract(**overrides):
    """Build a minimal valid .fawkespipe.yml contract dict, with overrides merged in."""
    base = {
        "app": {"name": "my-app", "type": "service", "language": "python"},
        "build": {
            "builder": "cnb",
            "cnb": {"builder": "paketobuildpacks/builder:base"},
        },
        "stages": {
            "lint": {
                "enabled": True,
                "commands": [
                    {"language": "python", "cmd": "pylint src/"},
                    {"language": "java", "cmd": "mvn checkstyle:check"},
                ],
            },
            "test": {
                "enabled": True,
                "commands": [
                    {"language": "python", "cmd": "pytest tests/"},
                    {"language": "java", "cmd": "mvn test"},
                ],
            },
            "sast": {"enabled": True},
            "dependency_scan": {"enabled": True},
            "build": {"enabled": True},
            "image_scan": {"enabled": True},
            "push": {"enabled": True},
        },
        "advanced": {"timeout": 60},
    }
    for key, value in overrides.items():
        base[key] = value
    return base


@pytest.mark.unit
class TestStageToggles:
    def test_disabled_lint_stage_produces_no_lint_step(self):
        contract = _contract()
        contract["stages"]["lint"]["enabled"] = False
        rendered = gen.render(contract)
        pipeline = yaml.safe_load(rendered)
        names = [s["name"] for s in pipeline["steps"]]
        assert "lint" not in names

    def test_enabled_lint_stage_produces_lint_step(self):
        pipeline = yaml.safe_load(gen.render(_contract()))
        names = [s["name"] for s in pipeline["steps"]]
        assert "lint" in names

    def test_all_stages_disabled_raises(self):
        contract = _contract()
        for stage in contract["stages"].values():
            stage["enabled"] = False
        with pytest.raises(gen.ContractError):
            gen.render(contract)


@pytest.mark.unit
class TestLanguageSelection:
    def test_python_language_uses_python_test_command(self):
        pipeline = yaml.safe_load(gen.render(_contract()))
        test_step = next(s for s in pipeline["steps"] if s["name"] == "test")
        assert "pytest" in " ".join(test_step["commands"])
        assert "mvn" not in " ".join(test_step["commands"])

    def test_java_language_uses_java_test_command(self):
        contract = _contract()
        contract["app"]["language"] = "java"
        pipeline = yaml.safe_load(gen.render(contract))
        test_step = next(s for s in pipeline["steps"] if s["name"] == "test")
        assert "mvn" in " ".join(test_step["commands"])

    def test_language_missing_from_stage_commands_raises(self):
        contract = _contract()
        contract["app"]["language"] = "go"
        with pytest.raises(gen.ContractError):
            gen.render(contract)


@pytest.mark.unit
class TestBuilderSelection:
    def test_cnb_builder_uses_pack_build(self):
        pipeline = yaml.safe_load(gen.render(_contract()))
        build_step = next(s for s in pipeline["steps"] if s["name"] == "build")
        assert "pack build" in " ".join(build_step["commands"])

    def test_docker_builder_uses_docker_build(self):
        contract = _contract()
        contract["build"] = {
            "builder": "docker",
            "docker": {"dockerfile": "Dockerfile", "context": "."},
        }
        pipeline = yaml.safe_load(gen.render(contract))
        build_step = next(s for s in pipeline["steps"] if s["name"] == "build")
        assert "docker build" in " ".join(build_step["commands"])

    def test_unsupported_builder_raises(self):
        contract = _contract()
        contract["build"] = {"builder": "bazel"}
        with pytest.raises(gen.ContractError):
            gen.render(contract)


@pytest.mark.unit
class TestTimeout:
    def test_timeout_is_reflected_in_generated_output(self):
        rendered = gen.render(_contract())
        assert "60" in rendered
        assert "timeout" in rendered.lower()


@pytest.mark.unit
class TestContractLoading:
    def test_missing_contract_file_raises_actionable_error(self, tmp_path):
        missing = tmp_path / ".fawkespipe.yml"
        with pytest.raises(gen.ContractError, match="not found"):
            gen.load_contract(missing)

    def test_malformed_yaml_raises_actionable_error(self, tmp_path):
        bad = tmp_path / ".fawkespipe.yml"
        bad.write_text("app:\n  name: [unclosed")
        with pytest.raises(gen.ContractError):
            gen.load_contract(bad)

    def test_missing_app_language_raises(self, tmp_path):
        contract_file = tmp_path / ".fawkespipe.yml"
        contract_file.write_text(yaml.safe_dump({"app": {"name": "x"}}))
        with pytest.raises(gen.ContractError, match="app.language"):
            gen.load_contract(contract_file)

    def test_valid_contract_loads(self, tmp_path):
        contract_file = tmp_path / ".fawkespipe.yml"
        contract_file.write_text(yaml.safe_dump(_contract()))
        loaded = gen.load_contract(contract_file)
        assert loaded["app"]["language"] == "python"


@pytest.mark.unit
class TestCheckMode:
    def test_check_passes_when_output_matches(self, tmp_path):
        contract_file = tmp_path / ".fawkespipe.yml"
        contract_file.write_text(yaml.safe_dump(_contract()))
        output_file = tmp_path / ".woodpecker.yml"
        assert (
            gen.main(["--contract", str(contract_file), "--output", str(output_file)])
            == 0
        )
        assert (
            gen.main(
                [
                    "--contract",
                    str(contract_file),
                    "--output",
                    str(output_file),
                    "--check",
                ]
            )
            == 0
        )

    def test_check_fails_when_output_is_stale(self, tmp_path):
        contract_file = tmp_path / ".fawkespipe.yml"
        contract_file.write_text(yaml.safe_dump(_contract()))
        output_file = tmp_path / ".woodpecker.yml"
        output_file.write_text("steps: []\n")
        assert (
            gen.main(
                [
                    "--contract",
                    str(contract_file),
                    "--output",
                    str(output_file),
                    "--check",
                ]
            )
            == 1
        )

    def test_check_fails_when_output_missing(self, tmp_path):
        contract_file = tmp_path / ".fawkespipe.yml"
        contract_file.write_text(yaml.safe_dump(_contract()))
        output_file = tmp_path / ".woodpecker.yml"
        assert (
            gen.main(
                [
                    "--contract",
                    str(contract_file),
                    "--output",
                    str(output_file),
                    "--check",
                ]
            )
            == 1
        )

    def test_main_exits_nonzero_on_missing_contract(self, tmp_path, capsys):
        missing = tmp_path / ".fawkespipe.yml"
        output_file = tmp_path / ".woodpecker.yml"
        assert gen.main(["--contract", str(missing), "--output", str(output_file)]) == 1
        assert "error" in capsys.readouterr().err.lower()


@pytest.mark.unit
class TestMigrationExample:
    """examples/fawkespipe-contract-migration/ (PIPE-009 AC-01, AC-02)."""

    EXAMPLE_DIR = (
        Path(__file__).resolve().parents[2]
        / "examples"
        / "fawkespipe-contract-migration"
    )

    def test_generated_output_matches_checked_in_woodpecker_yml(self):
        contract = gen.load_contract(self.EXAMPLE_DIR / ".fawkespipe.yml")
        rendered = gen.render(contract)
        assert rendered == (self.EXAMPLE_DIR / ".woodpecker.yml").read_text()

    def test_disabled_push_stage_is_absent(self):
        pipeline = yaml.safe_load((self.EXAMPLE_DIR / ".woodpecker.yml").read_text())
        names = [s["name"] for s in pipeline["steps"]]
        assert "push" not in names

    def test_python_language_command_is_used(self):
        pipeline = yaml.safe_load((self.EXAMPLE_DIR / ".woodpecker.yml").read_text())
        test_step = next(s for s in pipeline["steps"] if s["name"] == "test")
        assert "pytest" in " ".join(test_step["commands"])
