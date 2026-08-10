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

STAGE_ORDER = ("lint", "test", "sast", "dependency_scan", "build", "image_scan", "push")

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
    return {
        "name": "sast",
        "image": "sonarsource/sonar-scanner-cli:latest",
        "commands": ["sonar-scanner"],
    }


def _dependency_scan_step(contract: dict) -> dict:
    return {
        "name": "dependency-scan",
        "image": "aquasec/trivy:latest",
        "commands": ["trivy fs --exit-code 1 ."],
    }


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
        "commands": ["trivy image --exit-code 1 $CI_REPO_NAME"],
    }


def _push_step(contract: dict) -> dict:
    return {
        "name": "push",
        "image": "docker:24-cli",
        "commands": ["docker push $CI_REPO_NAME"],
    }


_STEP_BUILDERS = {
    "lint": _lint_step,
    "test": _test_step,
    "sast": _sast_step,
    "dependency_scan": _dependency_scan_step,
    "build": _build_step,
    "image_scan": _image_scan_step,
    "push": _push_step,
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
