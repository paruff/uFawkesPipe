"""Tests for scripts/generate_woodpecker_yml.py.

Encodes docs/ai-sdlc/v2.0.0/consolidate-sec-spec.md (PIPE-009) AC-01..AC-04 against the field -> step
mapping documented in docs/ai-sdlc/v2.0.0/consolidate-sec-design.md §5.
"""

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import generate_woodpecker_yml as gen


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


def _step(contract, name):
    pipeline = yaml.safe_load(gen.render(contract))
    return next((s for s in pipeline["steps"] if s["name"] == name), None)


@pytest.mark.unit
class TestCnbBuildPublishes:
    """AC-PIPE-01: the contract's CNB build must be a real build that publishes
    an image. `pack` isn't in docker:24-cli, so the old step could never run."""

    def test_cnb_build_runs_in_a_pinned_pack_image(self):
        image = _step(_contract(), "build")["image"]
        assert image.startswith("buildpacksio/pack:")
        assert not image.endswith(":latest")

    def test_cnb_build_publishes_to_the_registry_user_namespace(self):
        cmds = " ".join(_step(_contract(), "build")["commands"])
        assert "--publish" in cmds
        assert "${REGISTRY_USERNAME}/${CI_REPO_NAME}:${CI_COMMIT_SHA:0:7}" in cmds

    def test_cnb_build_reads_the_registry_secrets(self):
        env = _step(_contract(), "build")["environment"]
        assert env["REGISTRY_USERNAME"] == {"from_secret": "registry_username"}
        assert env["REGISTRY_PASSWORD"] == {"from_secret": "registry_password"}

    def test_cnb_build_honours_the_contract_image_name(self):
        contract = _contract()
        contract["build"]["image"] = {"namespace": "paruff", "name": "sample"}
        cmds = " ".join(_step(contract, "build")["commands"])
        assert "paruff/sample:${CI_COMMIT_SHA:0:7}" in cmds

    def test_cnb_emits_no_push_step_because_build_already_published(self):
        assert _step(_contract(), "push") is None

    def test_docker_builder_still_emits_a_push_step(self):
        contract = _contract()
        contract["build"] = {"builder": "docker", "docker": {"dockerfile": "Dockerfile"}}
        assert _step(contract, "push") is not None


@pytest.mark.unit
class TestNotifyObsStage:
    def _enabled(self):
        contract = _contract()
        contract["stages"]["notify_obs"] = {"enabled": True}
        return contract

    def test_absent_by_default(self):
        assert _step(_contract(), "notify-obs") is None

    def test_runs_last_on_main_pushes_even_after_a_failure(self):
        pipeline = yaml.safe_load(gen.render(self._enabled()))
        step = pipeline["steps"][-1]
        assert step["name"] == "notify-obs"
        assert step["when"] == {"event": "push", "branch": "main"}
        assert step["runs_on"] == ["success", "failure"]

    def test_never_fails_the_pipeline(self):
        assert _step(self._enabled(), "notify-obs")["failure"] == "ignore"

    def test_reads_ingestion_url_and_optional_key_from_secrets(self):
        env = _step(self._enabled(), "notify-obs")["environment"]
        assert env["DORA_INGESTION_URL"] == {"from_secret": "dora_ingestion_url"}
        assert env["DORA_API_KEY"] == {"from_secret": "dora_api_key"}

    def _run(self, tmp_path, status):
        """Run the generated commands with a stub curl; return (exit code, request)."""
        import json
        import os
        import subprocess

        stub = tmp_path / "curl"
        stub.write_text(
            '#!/bin/sh\n'
            'for a in "$@"; do last="$a"; done\n'
            'printf "%s" "$last" > "$CURL_BODY"\n'
            'printf "%s\\n" "$@" > "$CURL_ARGS"\n'
            'printf 201\n'
        )
        stub.chmod(0o755)
        env = {
            "PATH": f"{tmp_path}:/usr/bin:/bin",
            "CURL_BODY": str(tmp_path / "body"),
            "CURL_ARGS": str(tmp_path / "args"),
            "DORA_INGESTION_URL": "http://dora-api:8088",
            "CI_REPO": "paruff/sample",
            "CI_REPO_NAME": "sample",
            "CI_COMMIT_SHA": "a" * 40,
            "CI_PIPELINE_URL": "http://woodpecker/repos/1/pipeline/1",
            "CI_PIPELINE_STATUS": status,
        }
        script = "\n".join(_step(self._enabled(), "notify-obs")["commands"])
        done = subprocess.run(["sh", "-c", script], env=env, capture_output=True, text=True)
        body = (tmp_path / "body").read_text() if (tmp_path / "body").exists() else ""
        return done, json.loads(body) if body else None, tmp_path

    def test_posts_a_schema_shaped_deployment_event(self, tmp_path):
        done, event, _ = self._run(tmp_path, "success")
        assert done.returncode == 0, done.stderr
        assert event["schema_version"] == "1.0"
        assert event["event_type"] == "deployment"
        assert event["repo"] == "paruff/sample"
        assert event["service"] == "sample"
        assert event["commit_sha"] == "a" * 40
        assert event["status"] == "success"
        assert event["pipeline_url"] == "http://woodpecker/repos/1/pipeline/1"
        assert event["deployed_at"].endswith("Z")

    def test_a_failed_pipeline_is_sent_as_failed(self, tmp_path):
        _, event, _ = self._run(tmp_path, "failure")
        assert event["status"] == "failed"

    def test_posts_to_the_event_endpoint(self, tmp_path):
        _, _, tmp = self._run(tmp_path, "success")
        assert "http://dora-api:8088/event" in (tmp / "args").read_text()

    def test_step_fails_visibly_when_ingestion_url_is_unset(self, tmp_path):
        import subprocess

        script = "\n".join(_step(self._enabled(), "notify-obs")["commands"])
        done = subprocess.run(
            ["sh", "-c", script], env={"PATH": "/usr/bin:/bin"}, capture_output=True, text=True
        )
        assert done.returncode != 0


@pytest.mark.unit
class TestCnbImageScanTargetsPublishedImage:
    def test_scans_the_tag_that_build_published(self):
        step = _step(_contract(), "image-scan")
        cmds = " ".join(step["commands"])
        assert "${REGISTRY_USERNAME}/${CI_REPO_NAME}:${CI_COMMIT_SHA:0:7}" in cmds
        assert step["environment"]["REGISTRY_USERNAME"] == {
            "from_secret": "registry_username"
        }

    def test_docker_builder_scan_is_unchanged(self):
        contract = _contract()
        contract["build"] = {"builder": "docker", "docker": {"dockerfile": "Dockerfile"}}
        step = _step(contract, "image-scan")
        assert "environment" not in step
        assert step["commands"][-1].endswith(" $CI_REPO_NAME")
