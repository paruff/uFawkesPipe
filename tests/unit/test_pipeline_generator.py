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
        """Acceptance: java maps to maven:3.9-eclipse-temurin-17."""
        assert _language_image("java") == "maven:3.9-eclipse-temurin-17"

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
        assert "bandit -r src/ -s HIGH -c HIGH" in commands_str, (
            "Bandit must use custom severity/confidence"
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
