# Security Policy

uFawkesPipe is a DevSecOps platform, so we hold its own security bar seriously.

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for a suspected vulnerability.

Instead, use [GitHub's private vulnerability reporting](https://github.com/paruff/uFawkesPipe/security/advisories/new) for this repository. Include:

- A description of the vulnerability and its impact
- Steps to reproduce (or a proof of concept)
- Affected version/commit

We'll acknowledge reports within 5 business days and aim to ship a fix or mitigation before any public disclosure.

## Supported Versions

Pre-1.0 (current): only the latest tagged release receives security fixes. There is no LTS branch yet — see `MILESTONES.md` for the v1.0 target.

## Scope

In scope: this repository's own code, scripts, and generated pipeline output (`scripts/generate_woodpecker_yml.py` and what it produces). Out of scope: the upstream tools it orchestrates (Woodpecker, SonarQube, Trivy, DefectDojo, etc.) — report those to their own maintainers.
