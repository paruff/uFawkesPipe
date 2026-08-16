"""Unit tests for compose.yaml and compose.suite.yaml structure.

Parses the YAML files with pyyaml and validates:
  - All core security-plane services present, plus embedded postgres/valkey
  - fawkes-net is an internal (non-external) network in compose.suite.yaml
  - defectdojo and infisical have healthcheck blocks
  - falco is the only service with privileged: true
  - No image tag is :latest
  - All secrets referenced in services are declared in top-level secrets
"""

import pytest
import yaml

CORE_SERVICES = {
    "defectdojo",
    "defectdojo-nginx",
    "defectdojo-celery-beat",
    "defectdojo-celery-worker",
    "infisical",
    "trivy-server",
    "falco",
}

STANDALONE_EXTRA = {"postgres", "valkey"}


@pytest.fixture
def compose_data(project_root):
    """Parse compose.yaml and return the dict."""
    path = project_root / "compose.yaml"
    assert path.exists(), f"Missing compose file: {path}"
    with open(path) as f:
        return yaml.safe_load(f)


@pytest.fixture
def suite_compose_data(project_root):
    """Parse compose.suite.yaml and return the dict."""
    path = project_root / "compose.suite.yaml"
    assert path.exists(), f"Missing compose file: {path}"
    with open(path) as f:
        return yaml.safe_load(f)


# ── Service Name Coverage ─────────────────────────────────────────────────


class TestServiceNames:
    """All core security-plane services must be present in compose.yaml."""

    def test_all_core_services_present(self, compose_data):
        services = set(compose_data.get("services", {}).keys())
        missing = CORE_SERVICES - services
        assert not missing, f"Missing expected core services: {missing}"

    def test_standalone_extra_services_present(self, compose_data):
        """compose.yaml embeds postgres and valkey directly (standalone mode)."""
        services = set(compose_data.get("services", {}).keys())
        missing = STANDALONE_EXTRA - services
        assert not missing, f"Missing embedded services: {missing}"
        vol_names = set(compose_data.get("volumes", {}).keys())
        assert "postgres-data" in vol_names, "Missing postgres-data volume"
        assert "valkey-data" in vol_names, "Missing valkey-data volume"


# ── Network Assertions ────────────────────────────────────────────────────


class TestNetwork:
    """fawkes-net is now an internal network owned by this repo's compose.suite.yaml."""

    def test_fawkes_net_is_internal(self, suite_compose_data):
        networks = suite_compose_data.get("networks", {})
        assert "fawkes-net" in networks, "fawkes-net not declared in networks"
        fawkes = networks["fawkes-net"]
        assert fawkes.get("external") is not True, (
            "fawkes-net must be internal now that uFawkesSec is merged into this repo"
        )

    def test_fawkes_net_has_name(self, suite_compose_data):
        networks = suite_compose_data.get("networks", {})
        fawkes = networks.get("fawkes-net", {})
        assert fawkes.get("name") == "fawkes-net", (
            "fawkes-net must have explicit name: fawkes-net"
        )

    def test_all_services_on_fawkes_net(self, suite_compose_data):
        """Every service declared in compose.suite.yaml must be on fawkes-net."""
        services = suite_compose_data.get("services", {})
        for svc_name, svc_config in services.items():
            svc_networks = svc_config.get("networks", [])
            if isinstance(svc_networks, list):
                assert "fawkes-net" in svc_networks, (
                    f"Service '{svc_name}' is not on fawkes-net"
                )
            elif isinstance(svc_networks, dict):
                assert "fawkes-net" in svc_networks, (
                    f"Service '{svc_name}' is not on fawkes-net"
                )


# ── Healthcheck Assertions ────────────────────────────────────────────────


class TestHealthchecks:
    """defectdojo and infisical must have healthcheck blocks."""

    def test_defectdojo_has_healthcheck(self, compose_data):
        svc = compose_data["services"].get("defectdojo", {})
        assert "healthcheck" in svc, "defectdojo is missing a healthcheck block"
        hc = svc["healthcheck"]
        assert "test" in hc, "defectdojo healthcheck has no test command"
        assert "interval" in hc, "defectdojo healthcheck has no interval"
        assert "retries" in hc, "defectdojo healthcheck has no retries"

    def test_infisical_has_healthcheck(self, compose_data):
        svc = compose_data["services"].get("infisical", {})
        assert "healthcheck" in svc, "infisical is missing a healthcheck block"
        hc = svc["healthcheck"]
        assert "test" in hc, "infisical healthcheck has no test command"
        assert "interval" in hc, "infisical healthcheck has no interval"
        assert "retries" in hc, "infisical healthcheck has no retries"

    def test_trivy_server_has_healthcheck(self, compose_data):
        svc = compose_data["services"].get("trivy-server", {})
        assert "healthcheck" in svc, "trivy-server is missing a healthcheck block"

    def test_defectdojo_nginx_has_healthcheck(self, compose_data):
        svc = compose_data["services"].get("defectdojo-nginx", {})
        assert "healthcheck" in svc, "defectdojo-nginx is missing a healthcheck block"

    def test_defectdojo_celery_worker_has_healthcheck(self, compose_data):
        svc = compose_data["services"].get("defectdojo-celery-worker", {})
        assert "healthcheck" in svc, (
            "defectdojo-celery-worker is missing a healthcheck block"
        )

    def test_postgres_and_valkey_have_healthcheck(self, compose_data):
        for svc_name in ("postgres", "valkey"):
            svc = compose_data["services"].get(svc_name, {})
            assert "healthcheck" in svc, f"{svc_name} is missing a healthcheck block"

    def test_defectdojo_depends_on_postgres_and_valkey(self, compose_data):
        """defectdojo must wait for postgres and valkey to be healthy."""
        svc = compose_data["services"].get("defectdojo", {})
        depends = svc.get("depends_on", {})
        assert depends.get("postgres", {}).get("condition") == "service_healthy", (
            "defectdojo must wait for postgres healthy"
        )
        assert depends.get("valkey", {}).get("condition") == "service_healthy", (
            "defectdojo must wait for valkey healthy"
        )


# ── Privileged Assertions ─────────────────────────────────────────────────


class TestPrivileged:
    """falco is the only service with privileged: true."""

    def test_falco_is_privileged(self, compose_data):
        falco = compose_data["services"].get("falco", {})
        assert falco.get("privileged") is True, "falco must have privileged: true"

    def test_no_other_service_is_privileged(self, compose_data):
        services = compose_data.get("services", {})
        privileged_services = [
            name
            for name, config in services.items()
            if config.get("privileged") is True
        ]
        assert privileged_services == ["falco"], (
            f"Only falco should be privileged, but got: {privileged_services}"
        )


# ── Image Tag Assertions ──────────────────────────────────────────────────


class TestImageTags:
    """No :latest tags on any service."""

    def test_no_latest_tags(self, compose_data):
        services = compose_data.get("services", {})
        latest_services = [
            name
            for name, config in services.items()
            if ":latest" in config.get("image", "")
        ]
        assert not latest_services, f"Services with :latest tag: {latest_services}"


# ── Secret Assertions ─────────────────────────────────────────────────────


class TestSecrets:
    """All service secrets must be declared in top-level secrets block."""

    def test_secrets_top_level_declared(self, compose_data):
        top_secrets = set(compose_data.get("secrets", {}).keys())
        used_secrets = set()
        services = compose_data.get("services", {})
        for svc_name, svc_config in services.items():
            svc_secrets = svc_config.get("secrets", [])
            if isinstance(svc_secrets, list):
                for s in svc_secrets:
                    if isinstance(s, str):
                        used_secrets.add(s)
                    elif isinstance(s, dict):
                        # secret reference with source/key format
                        used_secrets.update(s.values())
                        used_secrets.update(s.keys())
            elif isinstance(svc_secrets, dict):
                # dict format: secret_name: {...}
                used_secrets.update(svc_secrets.keys())
        undeclared = used_secrets - top_secrets
        assert not undeclared, (
            f"Secrets used in services but not declared in top-level 'secrets:': "
            f"{undeclared}"
        )

    def test_secrets_use_environment_source(self, compose_data):
        """All secrets should use the environment: injection syntax."""
        secrets = compose_data.get("secrets", {})
        for name, config in secrets.items():
            assert "environment" in config, (
                f"Secret '{name}' should use environment: source, got: {list(config.keys())}"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
