"""Tests for scripts/generate_woodpecker_yml.py pipeline contract generator.

Validates edge cases: empty stages, custom builders, missing required fields,
minimal valid config, and error handling.
"""

import pytest
import yaml
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from generate_woodpecker_yml import (
    ContractError,
    load_contract,
    render,
    _stage_enabled,
    _language_image,
)


@pytest.fixture
def tmp_contract(tmp_path):
    """Create a temporary .fawkespipe.yml contract file."""

    def _make_contract(content: dict) -> Path:
        contract_path = tmp_path / ".fawkespipe.yml"
        contract_path.write_text(yaml.safe_dump(content))
        return contract_path

    return _make_contract


@pytest.mark.unit
class TestLoadContract:
    """Test contract loading and validation."""

    def test_missing_file_raises_error(self, tmp_path):
        """Acceptance: Missing contract file raises ContractError."""
        missing = tmp_path / ".fawkespipe.yml"
        with pytest.raises(ContractError, match="not found"):
            load_contract(missing)

    def test_invalid_yaml_raises_error(self, tmp_path):
        """Acceptance: Invalid YAML raises ContractError."""
        contract_path = tmp_path / ".fawkespipe.yml"
        contract_path.write_text("invalid: yaml: [}")
        with pytest.raises(ContractError, match="not valid YAML"):
            load_contract(contract_path)

    def test_missing_app_language_raises_error(self, tmp_contract):
        """Acceptance: Missing app.language raises ContractError."""
        contract_path = tmp_contract({"app": {"name": "test"}})
        with pytest.raises(ContractError, match="missing required field"):
            load_contract(contract_path)

    def test_valid_minimal_contract(self, tmp_contract):
        """Acceptance: Minimal valid contract loads successfully."""
        contract_path = tmp_contract(
            {
                "app": {"name": "test", "language": "python"},
                "stages": {"test": {"enabled": True}},
            }
        )
        contract = load_contract(contract_path)
        assert contract["app"]["language"] == "python"


@pytest.mark.unit
class TestStageEnabled:
    """Test stage enablement logic."""

    def test_stage_not_present(self):
        """Acceptance: Missing stage returns False."""
        assert _stage_enabled({}, "lint") is False

    def test_stage_disabled(self):
        """Acceptance: Stage with enabled: false returns False."""
        contract = {"stages": {"lint": {"enabled": False}}}
        assert _stage_enabled(contract, "lint") is False

    def test_stage_enabled(self):
        """Acceptance: Stage with enabled: true returns True."""
        contract = {"stages": {"lint": {"enabled": True}}}
        assert _stage_enabled(contract, "lint") is True


@pytest.mark.unit
class TestLanguageImage:
    """Test language image mapping."""

    def test_python_image(self):
        """Acceptance: python maps to python:3.12-slim."""
        assert _language_image("python") == "python:3.12-slim"

    def test_java_image(self):
        """Acceptance: java maps to maven:3.9-eclipse-temurin-21."""
        assert _language_image("java") == "maven:3.9-eclipse-temurin-21"

    def test_go_image(self):
        """Acceptance: go maps to golang:1.22."""
        assert _language_image("go") == "golang:1.22"

    def test_nodejs_image(self):
        """Acceptance: nodejs maps to node:20-slim."""
        assert _language_image("nodejs") == "node:20-slim"

    def test_unsupported_language_raises_error(self):
        """Acceptance: Unsupported language raises ContractError."""
        with pytest.raises(ContractError, match="unsupported app.language"):
            _language_image("rust")


@pytest.mark.unit
class TestRenderMinimalContract:
    """Test rendering minimal valid contracts."""

    def test_single_test_stage(self):
        """Acceptance: Contract with only test stage produces one step."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                }
            },
        }
        result = render(contract)
        parsed = yaml.safe_load(result)
        assert "steps" in parsed
        assert len(parsed["steps"]) == 1
        assert parsed["steps"][0]["name"] == "test"

    def test_multiple_stages(self):
        """Acceptance: Contract with lint + test produces two steps."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "lint": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "ruff check"}],
                },
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }
        result = render(contract)
        parsed = yaml.safe_load(result)
        assert len(parsed["steps"]) == 2
        assert parsed["steps"][0]["name"] == "lint"
        assert parsed["steps"][1]["name"] == "test"

    def test_all_stages_disabled_raises_error(self):
        """Acceptance: All stages disabled raises ContractError."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "lint": {"enabled": False},
                "test": {"enabled": False},
            },
        }
        with pytest.raises(ContractError, match="no stages are enabled"):
            render(contract)


@pytest.mark.unit
class TestRenderEdgeCases:
    """Test edge cases in pipeline generation."""

    def test_empty_stages_dict(self):
        """Acceptance: Empty stages dict raises ContractError."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {},
        }
        with pytest.raises(ContractError, match="no stages are enabled"):
            render(contract)

    def test_custom_docker_builder(self):
        """Acceptance: Docker builder produces correct step."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "build": {
                "builder": "docker",
                "docker": {"dockerfile": "Dockerfile.prod", "context": "src/"},
            },
            "stages": {
                "build": {"enabled": True},
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }
        result = render(contract)
        parsed = yaml.safe_load(result)
        build_step = next(s for s in parsed["steps"] if s["name"] == "build")
        assert "docker build -f Dockerfile.prod" in build_step["commands"][0]
        assert "src/" in build_step["commands"][0]

    def test_unsupported_builder_raises_error(self):
        """Acceptance: Unsupported builder raises ContractError."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "build": {"builder": "bazel"},
            "stages": {
                "build": {"enabled": True},
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }
        with pytest.raises(ContractError, match="unsupported build.builder"):
            render(contract)

    def test_cnb_builder_default(self):
        """Acceptance: CNB builder uses default pack builder."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "build": {"builder": "cnb"},
            "stages": {
                "build": {"enabled": True},
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }
        result = render(contract)
        parsed = yaml.safe_load(result)
        build_step = next(s for s in parsed["steps"] if s["name"] == "build")
        assert "paketobuildpacks/builder:base" in build_step["commands"][0]

    def test_cnb_builder_custom(self):
        """Acceptance: CNB builder uses custom builder when specified."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "build": {"builder": "cnb", "cnb": {"builder": "my/custom-builder:latest"}},
            "stages": {
                "build": {"enabled": True},
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }
        result = render(contract)
        parsed = yaml.safe_load(result)
        build_step = next(s for s in parsed["steps"] if s["name"] == "build")
        assert "my/custom-builder:latest" in build_step["commands"][0]


@pytest.mark.unit
class TestSonarQubeQualityGate:
    """Test SonarQube quality gate wait in generated pipeline."""

    def test_quality_gate_enabled_adds_wait_command(self):
        """Acceptance: sonarqube.qualityGate: true adds quality gate wait command."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "sast": {
                    "enabled": True,
                    "sonarqube": {"qualityGate": True},
                },
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }
        result = render(contract)
        parsed = yaml.safe_load(result)
        sast_step = next(s for s in parsed["steps"] if s["name"] == "sast")
        commands_str = " ".join(sast_step["commands"])
        assert "qualitygates/project" in commands_str, (
            "SAST step must include quality gate wait when sonarqube.qualityGate: true"
        )

    def test_quality_gate_disabled_no_wait_command(self):
        """Acceptance: sonarqube.qualityGate: false omits quality gate wait command."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "sast": {
                    "enabled": True,
                    "sonarqube": {"qualityGate": False},
                },
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }
        result = render(contract)
        parsed = yaml.safe_load(result)
        sast_step = next(s for s in parsed["steps"] if s["name"] == "sast")
        commands_str = " ".join(sast_step["commands"])
        assert "sonarqube-quality-gate" not in commands_str, (
            "SAST step must NOT include quality gate wait when sonarqube.qualityGate: false"
        )

    def test_quality_gate_default_is_true(self):
        """Acceptance: Default qualityGate is true when not specified."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "sast": {
                    "enabled": True,
                },
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }
        result = render(contract)
        parsed = yaml.safe_load(result)
        sast_step = next(s for s in parsed["steps"] if s["name"] == "sast")
        commands_str = " ".join(sast_step["commands"])
        assert "qualitygates/project" in commands_str, (
            "SAST step must include quality gate wait by default (qualityGate defaults to true)"
        )

    def test_quality_gate_uses_sonarqube_token(self):
        """Acceptance: Quality gate wait uses SONARQUBE_TOKEN from environment."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "sast": {
                    "enabled": True,
                    "sonarqube": {"qualityGate": True},
                },
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }
        result = render(contract)
        parsed = yaml.safe_load(result)
        sast_step = next(s for s in parsed["steps"] if s["name"] == "sast")
        commands_str = " ".join(sast_step["commands"])
        assert "SONARQUBE_TOKEN" in commands_str, (
            "Quality gate wait must use SONARQUBE_TOKEN environment variable"
        )

    def test_quality_gate_polls_until_complete(self):
        """Acceptance: Quality gate wait polls until status is not 'PENDING'."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "sast": {
                    "enabled": True,
                    "sonarqube": {"qualityGate": True},
                },
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }
        result = render(contract)
        parsed = yaml.safe_load(result)
        sast_step = next(s for s in parsed["steps"] if s["name"] == "sast")
        commands_str = " ".join(sast_step["commands"])
        assert "PENDING" in commands_str, (
            "Quality gate wait must poll until status is not 'PENDING'"
        )


@pytest.mark.unit
class TestRenderOutputFormat:
    """Test output format of rendered pipeline."""

    def test_header_contains_generated_comment(self):
        """Acceptance: Output starts with generated comment."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                }
            },
        }
        result = render(contract)
        assert result.startswith("# Generated by scripts/generate_woodpecker_yml.py")

    def test_timeout_comment_when_specified(self):
        """Acceptance: Timeout comment appears when advanced.timeout is set."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "advanced": {"timeout": 30},
            "stages": {
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                }
            },
        }
        result = render(contract)
        assert "advanced.timeout: 30" in result

    def test_no_timeout_comment_when_not_specified(self):
        """Acceptance: No timeout comment when advanced.timeout is not set."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                }
            },
        }
        result = render(contract)
        assert "advanced.timeout" not in result

    def test_step_depends_on_lint(self):
        """Acceptance: Test step depends on lint when lint is enabled."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "lint": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "ruff check"}],
                },
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }
        result = render(contract)
        parsed = yaml.safe_load(result)
        test_step = parsed["steps"][1]
        assert test_step["depends_on"] == ["lint"]


@pytest.mark.unit
class TestBanditInSast:
    """Test Bandit Python security linting in SAST stage."""

    def test_bandit_enabled_adds_bandit_commands(self):
        """Acceptance: bandit.enabled adds bandit commands to SAST."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "sast": {
                    "enabled": True,
                    "bandit": {"enabled": True},
                },
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }
        result = render(contract)
        parsed = yaml.safe_load(result)
        sast_step = next(s for s in parsed["steps"] if s["name"] == "sast")
        commands_str = " ".join(sast_step["commands"])
        assert "bandit -r src/" in commands_str, (
            "SAST step must include bandit when bandit.enabled: true"
        )

    def test_bandit_disabled_omits_bandit_commands(self):
        """Acceptance: bandit.enabled: false omits bandit commands."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "sast": {
                    "enabled": True,
                    "bandit": {"enabled": False},
                },
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }
        result = render(contract)
        parsed = yaml.safe_load(result)
        sast_step = next(s for s in parsed["steps"] if s["name"] == "sast")
        commands_str = " ".join(sast_step["commands"])
        assert "bandit" not in commands_str, (
            "SAST step must NOT include bandit when bandit.enabled: false"
        )

    def test_bandit_custom_severity_confidence(self):
        """Acceptance: Custom bandit severity/confidence used in commands."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "sast": {
                    "enabled": True,
                    "bandit": {
                        "enabled": True,
                        "severity": "HIGH",
                        "confidence": "HIGH",
                    },
                },
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }
        result = render(contract)
        parsed = yaml.safe_load(result)
        sast_step = next(s for s in parsed["steps"] if s["name"] == "sast")
        commands_str = " ".join(sast_step["commands"])
        assert (
            "bandit -r src/ --severity-level high --confidence-level high"
            in commands_str
        ), (
            "Bandit must use custom severity/confidence via --severity-level/--confidence-level "
            "(lowercase) — bandit's -s/-c flags are --skips/--config, not thresholds"
        )

    def test_bandit_gating_command_is_actually_valid(self):
        """Regression: the generated bandit gate command must be accepted by
        real bandit, not just contain the right substring. -s/-c and
        --exit-code previously shipped as unrecognized/wrong flags and never
        failed a build regardless of findings.

        Skipped when the bandit binary isn't on PATH — it's not a declared
        dependency of this repo (only of pipelines it generates for other
        repos), so it's not guaranteed to be installed in CI. Flags were
        verified once, for real, against a local bandit install."""
        import shutil
        import subprocess

        if shutil.which("bandit") is None:
            pytest.skip("bandit binary not on PATH")

        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "sast": {
                    "enabled": True,
                    "bandit": {
                        "enabled": True,
                        "severity": "HIGH",
                        "confidence": "HIGH",
                    },
                },
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }
        result = render(contract)
        parsed = yaml.safe_load(result)
        sast_step = next(s for s in parsed["steps"] if s["name"] == "sast")
        gate_cmd = next(
            c for c in sast_step["commands"] if c.startswith("bandit") and "-o" not in c
        )
        # swap the contract's placeholder "src/" target for a real directory
        # bandit can actually scan, without changing any of the flags under test
        real_target = str(Path(__file__).parent.parent.parent / "scripts")
        args = [real_target if a == "src/" else a for a in gate_cmd.split()]

        proc = subprocess.run(args, capture_output=True, text=True)
        assert proc.returncode in (0, 1), (
            f"bandit rejected the generated flags (exit {proc.returncode}): {proc.stderr}"
        )


@pytest.mark.unit
class TestDastStage:
    """Test DAST stage generation."""

    def test_dast_enabled_adds_zap_commands(self):
        """Acceptance: dast.enabled adds ZAP commands to pipeline."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "dast": {
                    "enabled": True,
                    "target_url": "http://my-app:8000",
                },
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }
        result = render(contract)
        parsed = yaml.safe_load(result)
        dast_step = next(s for s in parsed["steps"] if s["name"] == "dast")
        commands_str = " ".join(dast_step["commands"])
        assert "zap-baseline.py" in commands_str, (
            "DAST step must include zap-baseline.py when dast.enabled: true"
        )
        assert "zap-api-scan.py" in commands_str, (
            "DAST step must include zap-api-scan.py"
        )
        assert dast_step["image"] == "zaproxy/zap-stable:latest", (
            "owasp/zap2docker-stable is retired and unpullable — must use the "
            "maintained zaproxy/zap-stable image"
        )
        assert "|| true" not in commands_str, (
            "DAST commands must not swallow their exit code — a gate that can "
            "never fail isn't a gate"
        )
        assert " -P 300" not in commands_str, (
            "-P sets the ZAP listen port, not a timeout — using 300 there binds "
            "a privileged port instead of applying a scan timeout"
        )
        # fail_on defaults to HIGH -> only FAIL-level alerts break the build
        assert " -I" in commands_str, "default fail_on: HIGH must pass -I to ZAP"

    def test_dast_fail_on_non_high_does_not_ignore_warnings(self):
        """Acceptance: fail_on other than HIGH must fail the build on WARN too."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "dast": {
                    "enabled": True,
                    "target_url": "http://my-app:8000",
                    "fail_on": "LOW",
                },
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }
        result = render(contract)
        parsed = yaml.safe_load(result)
        dast_step = next(s for s in parsed["steps"] if s["name"] == "dast")
        commands_str = " ".join(dast_step["commands"])
        assert " -I" not in commands_str, (
            "fail_on: LOW must not ignore WARN-level alerts"
        )

    def test_dast_timeout_converted_to_zap_minutes(self):
        """Acceptance: contract timeout (seconds) maps to ZAP's -T (minutes)."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "dast": {
                    "enabled": True,
                    "target_url": "http://my-app:8000",
                    "timeout": 600,
                },
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }
        result = render(contract)
        parsed = yaml.safe_load(result)
        dast_step = next(s for s in parsed["steps"] if s["name"] == "dast")
        commands_str = " ".join(dast_step["commands"])
        assert " -T 10 " in commands_str, "600s timeout must render as -T 10 (minutes)"

    def test_dast_disabled_no_dast_step(self):
        """Acceptance: dast.enabled: false omits DAST step."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "dast": {"enabled": False},
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }
        result = render(contract)
        parsed = yaml.safe_load(result)
        step_names = [s["name"] for s in parsed["steps"]]
        assert "dast" not in step_names, (
            "DAST step must not exist when dast.enabled: false"
        )

    def test_dast_requires_target_url(self):
        """Acceptance: dast requires target_url when enabled."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "dast": {"enabled": True},
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }
        from generate_woodpecker_yml import ContractError

        with pytest.raises(ContractError, match="target_url is required"):
            render(contract)

    def test_dast_unsupported_tool_raises(self):
        """Acceptance: Unsupported dast.tool raises ContractError."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "dast": {
                    "enabled": True,
                    "target_url": "http://app:8000",
                    "tool": "burp",
                },
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }
        from generate_woodpecker_yml import ContractError

        with pytest.raises(ContractError, match="unsupported dast.tool"):
            render(contract)


@pytest.mark.unit
class TestDeployStage:
    """Test deploy stage generation for each target."""

    def _contract(self, deploy_cfg):
        return {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "deploy": {"enabled": True, **deploy_cfg},
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }

    def test_deploy_docker_target(self):
        result = render(self._contract({"target": "docker"}))
        parsed = yaml.safe_load(result)
        deploy_step = next(s for s in parsed["steps"] if s["name"] == "deploy")
        assert "docker run" in " ".join(deploy_step["commands"])

    def test_deploy_ssh_target_does_not_raise(self):
        """Regression: deploy.target: ssh previously raised NameError on every
        call (single-brace f-string tried to evaluate REGISTRY_USERNAME etc.
        as Python names instead of emitting literal ${VAR} text)."""
        contract = self._contract(
            {"target": "ssh", "host": "example.com", "ssh_key": "/keys/id_rsa"}
        )
        result = render(contract)  # must not raise NameError
        parsed = yaml.safe_load(result)
        deploy_step = next(s for s in parsed["steps"] if s["name"] == "deploy")
        cmd = deploy_step["commands"][0]
        assert "ssh -i /keys/id_rsa" in cmd
        assert (
            '"docker pull ${REGISTRY_USERNAME}/${CI_REPO_NAME}:${CI_COMMIT_SHA:0:7}'
            in cmd
        ), (
            "remote command must be double-quoted so the LOCAL shell expands "
            "Woodpecker vars before ssh sends them — the remote host has no "
            "REGISTRY_USERNAME/CI_REPO_NAME/CI_COMMIT_SHA of its own"
        )

    def test_deploy_ssh_requires_host_and_key(self):
        with pytest.raises(ContractError, match="deploy.host is required"):
            render(self._contract({"target": "ssh", "ssh_key": "/keys/id_rsa"}))
        with pytest.raises(ContractError, match="deploy.ssh_key is required"):
            render(self._contract({"target": "ssh", "host": "example.com"}))


@pytest.mark.unit
class TestDependencyScanTools:
    """P3-10: dependency_scan.tools selects the scanning tool used."""

    def _contract(self, dep_cfg):
        return {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "dependency_scan": {"enabled": True, **dep_cfg},
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
            },
        }

    def test_default_tool_is_trivy_and_writes_report(self):
        result = render(self._contract({}))
        parsed = yaml.safe_load(result)
        step = next(s for s in parsed["steps"] if s["name"] == "dependency-scan")
        commands_str = " ".join(step["commands"])
        assert "trivy fs --exit-code 1" in commands_str
        assert "artifacts/security/trivy-repo.json" in commands_str

    def test_osv_scanner_tool_selected(self):
        result = render(self._contract({"tools": ["osv-scanner"]}))
        parsed = yaml.safe_load(result)
        step = next(s for s in parsed["steps"] if s["name"] == "dependency-scan")
        assert step["image"] == "ghcr.io/google/osv-scanner:latest"
        commands_str = " ".join(step["commands"])
        assert "osv-scanner scan source" in commands_str
        assert "artifacts/security/osv.json" in commands_str

    def test_osv_scanner_licenses_flag(self):
        result = render(
            self._contract(
                {"tools": ["osv-scanner"], "licenses": ["MIT", "Apache-2.0"]}
            )
        )
        parsed = yaml.safe_load(result)
        step = next(s for s in parsed["steps"] if s["name"] == "dependency-scan")
        assert "--licenses=MIT,Apache-2.0" in " ".join(step["commands"])

    def test_osv_scanner_command_is_actually_valid(self):
        """Regression: run the generated osv-scanner command for real against
        a small real directory, the same way the bandit gate command is
        checked, since guessed-wrong CLI flags were the root cause of the
        Bandit/DAST bugs this queue item follows.

        Skipped when the osv-scanner binary isn't on PATH (it's a Go binary,
        not a pip dependency of this repo, so it's not on every dev/CI
        machine) — flags were verified once, for real, via
        `docker run ghcr.io/google/osv-scanner:latest` during development.
        """
        import shutil
        import subprocess

        if shutil.which("osv-scanner") is None:
            pytest.skip("osv-scanner binary not on PATH")

        result = render(self._contract({"tools": ["osv-scanner"]}))
        parsed = yaml.safe_load(result)
        step = next(s for s in parsed["steps"] if s["name"] == "dependency-scan")
        scan_cmd = next(c for c in step["commands"] if c.startswith("osv-scanner"))
        real_dir = str(Path(__file__).parent.parent.parent / "scripts")
        args = scan_cmd.replace(" -- .", f" -- {real_dir}").split()

        proc = subprocess.run(args, capture_output=True, text=True)
        assert proc.returncode in (0, 1), (
            f"osv-scanner rejected the generated flags (exit {proc.returncode}): {proc.stderr}"
        )

    def test_unsupported_tool_raises(self):
        with pytest.raises(ContractError, match="unsupported dependency_scan.tools"):
            render(self._contract({"tools": ["snyk"]}))


@pytest.mark.unit
class TestDefectDojoStage:
    """P2-1/P3-8/P3-9: DefectDojo ingestion of Trivy/Bandit/ZAP findings."""

    def _contract(self, defectdojo_cfg=None):
        stages = {
            "test": {
                "enabled": True,
                "commands": [{"language": "python", "cmd": "pytest"}],
            },
        }
        if defectdojo_cfg is not None:
            stages["defectdojo"] = {"enabled": True, **defectdojo_cfg}
        return {"app": {"name": "test", "language": "python"}, "stages": stages}

    def test_disabled_by_default(self):
        result = render(self._contract())
        parsed = yaml.safe_load(result)
        names = [s["name"] for s in parsed["steps"]]
        assert "defectdojo-upload" not in names

    def test_enabled_uploads_all_report_types(self):
        result = render(self._contract({}))
        parsed = yaml.safe_load(result)
        step = next(s for s in parsed["steps"] if s["name"] == "defectdojo-upload")
        commands_str = " ".join(step["commands"])
        for path, scan_type in [
            ("trivy-repo.json", "Trivy Scan"),
            ("trivy-image.json", "Trivy Scan"),
            ("bandit.json", "Bandit Scan"),
            ("zap-baseline.xml", "ZAP Scan"),
            ("zap-api.xml", "ZAP Scan"),
            ("osv.json", "OSV Scan"),
        ]:
            assert path in commands_str, f"missing upload for {path}"
            assert scan_type in commands_str, f"missing scan_type for {path}"

    def test_missing_report_file_does_not_fail_step(self):
        """Each upload is `[ -f path ] && curl ... || true` so a report a
        given pipeline never produced (e.g. bandit disabled) can't fail the
        step — matches the non-blocking pattern in this repo's own
        .woodpecker.yml upload-defectdojo step."""
        result = render(self._contract({}))
        parsed = yaml.safe_load(result)
        step = next(s for s in parsed["steps"] if s["name"] == "defectdojo-upload")
        upload_cmds = [c for c in step["commands"] if "import-scan" in c]
        assert upload_cmds, "expected at least one DefectDojo upload command"
        for cmd in upload_cmds:
            assert cmd.rstrip().endswith("|| true")

    def test_custom_url_and_engagement(self):
        result = render(
            self._contract(
                {"url": "http://dojo.internal:9000", "engagement_name": "nightly"}
            )
        )
        parsed = yaml.safe_load(result)
        step = next(s for s in parsed["steps"] if s["name"] == "defectdojo-upload")
        commands_str = " ".join(step["commands"])
        assert "http://dojo.internal:9000/api/v2/import-scan/" in commands_str
        assert "engagement_name=nightly" in commands_str

    def test_only_runs_on_push_to_main(self):
        result = render(self._contract({}))
        parsed = yaml.safe_load(result)
        step = next(s for s in parsed["steps"] if s["name"] == "defectdojo-upload")
        assert step["when"] == {"event": "push", "branch": "main"}

    def test_api_token_secret_is_wired(self):
        """Regression: commands reference $DEFECTDOJO_API_TOKEN, but Woodpecker
        does not auto-inject secrets — the step must declare
        environment.DEFECTDOJO_API_TOKEN.from_secret itself or the variable
        is empty at runtime and every upload silently sends no auth header."""
        result = render(self._contract({}))
        parsed = yaml.safe_load(result)
        step = next(s for s in parsed["steps"] if s["name"] == "defectdojo-upload")
        assert (
            step["environment"]["DEFECTDOJO_API_TOKEN"]["from_secret"]
            == "defectdojo_api_token"
        )


@pytest.mark.unit
class TestOtelTracing:
    """P3-4: OTEL span emission wired into curl-capable steps only."""

    def test_sast_dast_defectdojo_get_trace_prefix(self):
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
                "sast": {"enabled": True},
                "dast": {"enabled": True, "target_url": "http://app:8000"},
                "defectdojo": {"enabled": True},
            },
        }
        result = render(contract)
        parsed = yaml.safe_load(result)
        for name in ("sast", "dast", "defectdojo-upload"):
            step = next(s for s in parsed["steps"] if s["name"] == name)
            first_cmd = step["commands"][0]
            assert "source /drone/src/scripts/otel-trace.sh" in first_cmd
            assert f'otel_span_start "{name}"' in first_cmd
            assert "trap" in first_cmd and "otel_span_end" in first_cmd

    def test_lint_test_build_get_no_trace_prefix(self):
        """docker:24-cli, aquasec/trivy and python:3.12-slim have neither
        curl nor a POST-capable wget — confirmed while implementing P3-4 —
        so these steps are deliberately left uninstrumented."""
        contract = {
            "app": {"name": "test", "language": "python"},
            "stages": {
                "lint": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "ruff check ."}],
                },
                "test": {
                    "enabled": True,
                    "commands": [{"language": "python", "cmd": "pytest"}],
                },
                "build": {"enabled": True},
            },
        }
        result = render(contract)
        parsed = yaml.safe_load(result)
        for name in ("lint", "test", "build"):
            step = next(s for s in parsed["steps"] if s["name"] == name)
            assert "otel-trace.sh" not in " ".join(step["commands"])
