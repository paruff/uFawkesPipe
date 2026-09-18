#!/usr/bin/env python3
"""Generate .woodpecker.yml from an app repo's .fawkespipe.yml contract.

See design.md (PIPE-009) for the field -> step mapping this implements.

Usage:
    generate_woodpecker_yml.py [--contract PATH] [--output PATH] [--check]

--check regenerates in memory and compares against --output without writing;
exits 1 if they differ (or --output is missing) so it can gate CI on drift
between .fawkespipe.yml and the committed .woodpecker.yml.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

STAGE_ORDER = (
    "lint",
    "test",
    "sast",
    "dependency_scan",
    "build",
    "image_scan",
    "dast",
    "defectdojo",
    "push",
    "deploy",
)

# Shared workspace path where scan steps drop machine-readable reports for
# the defectdojo stage to pick up. Steps run in separate containers but
# share the Woodpecker workspace volume, so files written here by one step
# are visible to later steps in the same pipeline run.
ARTIFACTS_DIR = "artifacts/security"

_LANGUAGE_IMAGES = {
    "java": "maven:3.9-eclipse-temurin-17",
    "python": "python:3.12-slim",
    "nodejs": "node:20-slim",
    "go": "golang:1.22",
}


class ContractError(Exception):
    """Raised when .fawkespipe.yml is missing, malformed, or unsupported."""


def load_contract(path: Path) -> dict:
    if not path.is_file():
        raise ContractError(
            f"{path} not found — every app repo built by uFawkesPipe must have a .fawkespipe.yml at its root"
        )
    try:
        with path.open() as f:
            contract = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ContractError(f"{path} is not valid YAML: {exc}") from exc
    if not isinstance(contract, dict):
        raise ContractError(f"{path} must contain a YAML mapping at the top level")
    app = contract.get("app")
    if not isinstance(app, dict) or "language" not in app:
        raise ContractError(f"{path} is missing required field 'app.language'")
    return contract


def _stage_enabled(contract: dict, stage_name: str) -> bool:
    stage = contract.get("stages", {}).get(stage_name, {})
    return bool(stage.get("enabled", False))


def _language_image(language: str) -> str:
    if language not in _LANGUAGE_IMAGES:
        raise ContractError(
            f"unsupported app.language '{language}' — supported: {', '.join(sorted(_LANGUAGE_IMAGES))}"
        )
    return _LANGUAGE_IMAGES[language]


def _language_command(stage: dict, language: str, stage_name: str) -> str:
    for entry in stage.get("commands", []):
        if entry.get("language") == language:
            return entry["cmd"]
    raise ContractError(
        f"stages.{stage_name}.commands has no entry for app.language '{language}'"
    )


def _otel_trace_prefix(step_name: str) -> str:
    """P3-4: source the OTEL trace wrapper, start the span, and set a trap so
    otel_span_end fires with the real exit status even if a later command in
    this step fails under Woodpecker's default `set -e` (verified: a plain
    trailing call would never run once an earlier command aborts the step).
    Only used in steps whose image has curl (sonar-scanner-cli, zap-stable,
    curlimages/curl) — see scripts/otel-trace.sh for why the others don't."""
    return (
        "source /drone/src/scripts/otel-trace.sh && "
        f'otel_span_start "{step_name}" && '
        f'trap \'otel_span_end "{step_name}" "$([ "$?" = 0 ] && echo ok || echo error)"\' EXIT'
    )


def _lint_step(contract: dict) -> dict:
    language = contract["app"]["language"]
    return {
        "name": "lint",
        "image": _language_image(language),
        "commands": [_language_command(contract["stages"]["lint"], language, "lint")],
    }


def _test_step(contract: dict) -> dict:
    language = contract["app"]["language"]
    step = {
        "name": "test",
        "image": _language_image(language),
        "commands": [_language_command(contract["stages"]["test"], language, "test")],
    }
    if _stage_enabled(contract, "lint"):
        step["depends_on"] = ["lint"]
    return step


def _sast_step(contract: dict) -> dict:
    sast_cfg = contract.get("stages", {}).get("sast", {})
    sonarqube_cfg = sast_cfg.get("sonarqube", {})
    quality_gate = sonarqube_cfg.get("qualityGate", True)
    trivy_cfg = sast_cfg.get("trivy", {})
    trivy_enabled = trivy_cfg.get("enabled", True)
    bandit_cfg = sast_cfg.get("bandit", {})
    bandit_enabled = bandit_cfg.get("enabled", True)
    bandit_severity = bandit_cfg.get("severity", "MEDIUM")
    bandit_confidence = bandit_cfg.get("confidence", "MEDIUM")

    commands = [_otel_trace_prefix("sast"), "sonar-scanner"]

    if quality_gate:
        # Wait for SonarQube quality gate to complete
        # Polls the /api/qualitygates/project endpoint until status is not PENDING
        commands.append(
            'STATUS="PENDING"; '
            'while [ "$STATUS" = "PENDING" ]; do '
            "  sleep 5; "
            '  STATUS=$(curl -s -u "$SONARQUBE_TOKEN:" '
            '    "$SONARQUBE_URL/api/qualitygates/project?projectKey=$SONARQUBE_PROJECT_KEY" '
            "    | python3 -c \"import sys,json; print(json.load(sys.stdin).get('status','PENDING'))\"); "
            '  echo "Quality gate status: $STATUS"; '
            "done; "
            'if [ "$STATUS" != "OK" ]; then '
            '  echo "Quality gate failed with status: $STATUS"; '
            "  exit 1; "
            "fi"
        )

    if trivy_enabled:
        trivy_severity = trivy_cfg.get("severity", "HIGH,CRITICAL")
        commands.append(f"trivy fs --severity {trivy_severity} --exit-code 1 .")

    if bandit_enabled:
        commands.append(f"mkdir -p {ARTIFACTS_DIR}")
        commands.append(
            f"bandit -r src/ -ll -ii -f json -o {ARTIFACTS_DIR}/bandit.json || true"
        )
        # -s/--skips and -c/--config are different bandit flags; severity/confidence
        # thresholds are --severity-level/--confidence-level, values lowercase.
        # Bandit's own exit code is already non-zero when issues meet the
        # threshold, so no --exit-code flag exists (or is needed).
        commands.append(
            f"bandit -r src/ --severity-level {bandit_severity.lower()} "
            f"--confidence-level {bandit_confidence.lower()}"
        )

    return {
        "name": "sast",
        "image": "sonarsource/sonar-scanner-cli:latest",
        "commands": commands,
    }


def _dependency_scan_step(contract: dict) -> dict:
    dep_cfg = contract.get("stages", {}).get("dependency_scan", {})
    tools = dep_cfg.get("tools", ["trivy"])

    if tools == ["osv-scanner"]:
        licenses = dep_cfg.get("licenses", [])
        # --licenses reports on licenses against an allowlist; osv-scanner
        # itself exits non-zero on either a vulnerability or a license
        # outside the allowlist, so no separate --exit-code flag exists.
        license_flag = f" --licenses={','.join(licenses)}" if licenses else ""
        return {
            "name": "dependency-scan",
            "image": "ghcr.io/google/osv-scanner:latest",
            "commands": [
                f"mkdir -p {ARTIFACTS_DIR}",
                "osv-scanner scan source --recursive --format=json "
                f"--output-file={ARTIFACTS_DIR}/osv.json --all-packages"
                f"{license_flag} -- .",
            ],
        }

    if tools == ["trivy"]:
        return {
            "name": "dependency-scan",
            "image": "aquasec/trivy:latest",
            "commands": [
                f"mkdir -p {ARTIFACTS_DIR}",
                "trivy fs --exit-code 1 --format json "
                f"--output {ARTIFACTS_DIR}/trivy-repo.json .",
            ],
        }

    raise ContractError(
        f"unsupported dependency_scan.tools {tools} — supported: [trivy], [osv-scanner]"
    )


def _build_step(contract: dict) -> dict:
    build_cfg = contract.get("build", {})
    builder = build_cfg.get("builder", "cnb")
    if builder == "cnb":
        cnb_builder = build_cfg.get("cnb", {}).get(
            "builder", "paketobuildpacks/builder:base"
        )
        cmd = f"pack build $CI_REPO_NAME --builder {cnb_builder}"
    elif builder == "docker":
        docker_cfg = build_cfg.get("docker", {})
        dockerfile = docker_cfg.get("dockerfile", "Dockerfile")
        context = docker_cfg.get("context", ".")
        cmd = f"docker build -f {dockerfile} -t $CI_REPO_NAME {context}"
    else:
        raise ContractError(
            f"unsupported build.builder '{builder}' — supported: cnb, docker"
        )
    return {"name": "build", "image": "docker:24-cli", "commands": [cmd]}


def _image_scan_step(contract: dict) -> dict:
    return {
        "name": "image-scan",
        "image": "aquasec/trivy:latest",
        "commands": [
            f"mkdir -p {ARTIFACTS_DIR}",
            "trivy image --exit-code 1 --format json "
            f"--output {ARTIFACTS_DIR}/trivy-image.json $CI_REPO_NAME",
        ],
    }


def _dast_step(contract: dict) -> dict:
    dast_cfg = contract.get("stages", {}).get("dast", {})
    target_url = dast_cfg.get("target_url", "")
    tool = dast_cfg.get("tool", "zap")
    fail_on = dast_cfg.get("fail_on", "HIGH")
    timeout = dast_cfg.get("timeout", 300)
    # dast.rules ("Default Policy" in examples) has no wired ZAP config-file
    # equivalent yet — it would need a generated -c rules file, not just a name.
    # Not implemented; see docs/KNOWN_LIMITATIONS.md.

    if not target_url:
        raise ContractError("dast.target_url is required when dast.enabled is true")

    if tool != "zap":
        raise ContractError(f"unsupported dast.tool '{tool}' — supported: zap")

    # ZAP's own exit code is already non-zero on any WARN or FAIL alert.
    # fail_on: HIGH (default) means only FAIL-level alerts should break the
    # build, so pass -I to have ZAP ignore WARN-level ones.
    ignore_warn_flag = " -I" if fail_on == "HIGH" else ""
    # ZAP's -T is minutes; the contract's timeout is seconds.
    timeout_mins = max(1, round(timeout / 60))

    # ZAP baseline scan + active scan (exit code now propagates — no `|| true`).
    # -x writes the XML report DefectDojo's "ZAP Scan" parser reads; -r is
    # the human-readable HTML report.
    commands = [
        _otel_trace_prefix("dast"),
        f"mkdir -p {ARTIFACTS_DIR}",
        f"zap-baseline.py -t {target_url} -T {timeout_mins} "
        f"-r {ARTIFACTS_DIR}/zap-baseline.html -x {ARTIFACTS_DIR}/zap-baseline.xml"
        f"{ignore_warn_flag}",
        f"zap-api-scan.py -t {target_url}/openapi.json -f openapi -T {timeout_mins} "
        f"-r {ARTIFACTS_DIR}/zap-api.html -x {ARTIFACTS_DIR}/zap-api.xml{ignore_warn_flag}",
    ]

    return {
        "name": "dast",
        "image": "zaproxy/zap-stable:latest",
        "commands": commands,
    }


def _defectdojo_step(contract: dict) -> dict:
    dd_cfg = contract.get("stages", {}).get("defectdojo", {})
    url = dd_cfg.get("url", "http://defectdojo:8080")
    engagement = dd_cfg.get("engagement_name", "CI-Engagement")

    # (report path, DefectDojo parser name). A report that a given pipeline
    # never produced (e.g. bandit disabled) is silently skipped at runtime —
    # same non-blocking pattern as this repo's own .woodpecker.yml.
    # NOTE: "OSV Scan" is DefectDojo's documented parser name as of this
    # writing but hasn't been confirmed against a live DefectDojo instance
    # in this repo (none is running here) — verify before first real use.
    reports = [
        (f"{ARTIFACTS_DIR}/trivy-repo.json", "Trivy Scan"),
        (f"{ARTIFACTS_DIR}/trivy-image.json", "Trivy Scan"),
        (f"{ARTIFACTS_DIR}/bandit.json", "Bandit Scan"),
        (f"{ARTIFACTS_DIR}/zap-baseline.xml", "ZAP Scan"),
        (f"{ARTIFACTS_DIR}/zap-api.xml", "ZAP Scan"),
        (f"{ARTIFACTS_DIR}/osv.json", "OSV Scan"),
    ]
    commands = [_otel_trace_prefix("defectdojo-upload")] + [
        f'[ -f "{path}" ] && curl -sf -X POST "{url}/api/v2/import-scan/" '
        '-H "Authorization: Token $DEFECTDOJO_API_TOKEN" '
        '-F "active=true" -F "verified=false" '
        f'-F "scan_type={scan_type}" '
        f'-F "engagement_name={engagement}" '
        '-F "product_name=$CI_REPO_NAME" '
        f'-F "file=@{path}" || true'
        for path, scan_type in reports
    ]

    return {
        "name": "defectdojo-upload",
        "image": "curlimages/curl:8.6.0",
        # Woodpecker does not auto-inject secrets into a step's environment —
        # each one must be declared explicitly, same as this repo's own
        # upload-defectdojo step in .woodpecker.yml.
        "environment": {
            "DEFECTDOJO_API_TOKEN": {"from_secret": "defectdojo_api_token"}
        },
        "commands": commands,
        "when": {"event": "push", "branch": "main"},
    }


def _push_step(contract: dict) -> dict:
    return {
        "name": "push",
        "image": "docker:24-cli",
        "commands": ["docker push $CI_REPO_NAME"],
    }


def _deploy_step(contract: dict) -> dict:
    deploy_cfg = contract.get("stages", {}).get("deploy", {})
    target = deploy_cfg.get("target", "docker")

    if target == "docker":
        port = deploy_cfg.get("port", 8000)
        network = deploy_cfg.get("network", "ufawkespipe_default")
        env_file = deploy_cfg.get("env_file", "")
        env_file_flag = f" --env-file {env_file}" if env_file else ""
        commands = [
            f"docker run -d --name $CI_REPO_NAME "
            f"--network {network} "
            f"-p {port}:8000 "
            f"--restart unless-stopped "
            f"{env_file_flag} "
            f"${{REGISTRY_USERNAME}}/${{CI_REPO_NAME}}:${{CI_COMMIT_SHA:0:7}}",
        ]
    elif target == "compose":
        compose_file = deploy_cfg.get("compose_file", "docker-compose.yml")
        service_name = deploy_cfg.get("service_name", "$CI_REPO_NAME")
        commands = [
            f"docker compose -f {compose_file} up -d {service_name}",
        ]
    elif target == "ssh":
        host = deploy_cfg.get("host", "")
        user = deploy_cfg.get("user", "root")
        port = deploy_cfg.get("port", 22)
        ssh_key = deploy_cfg.get("ssh_key", "")
        if not host:
            raise ContractError("deploy.host is required when deploy.target is ssh")
        if not ssh_key:
            raise ContractError("deploy.ssh_key is required when deploy.target is ssh")
        # REGISTRY_USERNAME/CI_REPO_NAME/CI_COMMIT_SHA only exist in the deploy
        # container's own environment, not on the remote host — so the
        # remote command must be double-quoted, letting the LOCAL shell
        # expand them before ssh ever sends the string. Doubled braces
        # (${{VAR}}) make the f-string emit a literal ${VAR} for that local
        # shell to expand (single braces here previously raised NameError:
        # name 'REGISTRY_USERNAME' is not defined on every call).
        commands = [
            f"ssh -i {ssh_key} -p {port} {user}@{host} "
            f'"docker pull ${{REGISTRY_USERNAME}}/${{CI_REPO_NAME}}:${{CI_COMMIT_SHA:0:7}} && '
            f"docker stop ${{CI_REPO_NAME}} 2>/dev/null || true && "
            f"docker rm ${{CI_REPO_NAME}} 2>/dev/null || true && "
            f"docker run -d --name ${{CI_REPO_NAME}} -p 8000:8000 --restart unless-stopped "
            f'${{REGISTRY_USERNAME}}/${{CI_REPO_NAME}}:${{CI_COMMIT_SHA:0:7}}"',
        ]
    else:
        raise ContractError(
            f"unsupported deploy.target '{target}' — supported: docker, compose, ssh"
        )

    return {
        "name": "deploy",
        "image": "docker:24-cli",
        "commands": commands,
        "when": {
            "event": "push",
            "branch": "main",
        },
    }


_STEP_BUILDERS = {
    "lint": _lint_step,
    "test": _test_step,
    "sast": _sast_step,
    "dependency_scan": _dependency_scan_step,
    "build": _build_step,
    "image_scan": _image_scan_step,
    "dast": _dast_step,
    "defectdojo": _defectdojo_step,
    "push": _push_step,
    "deploy": _deploy_step,
}


def render(contract: dict) -> str:
    """Render full .woodpecker.yml text from a parsed .fawkespipe.yml contract."""
    steps = [
        _STEP_BUILDERS[name](contract)
        for name in STAGE_ORDER
        if _stage_enabled(contract, name)
    ]
    if not steps:
        raise ContractError(
            "no stages are enabled in .fawkespipe.yml — nothing to build"
        )

    header = [
        "# Generated by scripts/generate_woodpecker_yml.py from .fawkespipe.yml",
        "# Do not edit by hand — edit .fawkespipe.yml and run `make generate-pipeline`.",
        "# CI should run `generate_woodpecker_yml.py --check` to gate on drift.",
    ]
    timeout = contract.get("advanced", {}).get("timeout")
    if timeout is not None:
        header.append(
            f"# advanced.timeout: {timeout} minutes — Woodpecker CE has no native per-pipeline "
            "YAML timeout field; configure via repo settings (see docs/KNOWN_LIMITATIONS.md L-005)."
        )

    body = yaml.safe_dump({"steps": steps}, sort_keys=False)
    return "\n".join(header) + "\n\n" + body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", default=".fawkespipe.yml", type=Path)
    parser.add_argument("--output", default=".woodpecker.yml", type=Path)
    parser.add_argument(
        "--check", action="store_true", help="Check for drift without writing --output"
    )
    args = parser.parse_args(argv)

    try:
        contract = load_contract(args.contract)
        rendered = render(contract)
    except ContractError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.check:
        current = args.output.read_text() if args.output.is_file() else None
        if current != rendered:
            print(
                f"error: {args.output} is stale relative to {args.contract} — "
                "run `make generate-pipeline` and commit the result",
                file=sys.stderr,
            )
            return 1
        return 0

    args.output.write_text(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
