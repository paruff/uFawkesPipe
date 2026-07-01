---
name: security-agent
description: Security scanning configuration, secret detection, vulnerability policy specialist
applies: docker-compose.yml, .woodpecker.yml, .github/workflows/**/*.yml
---

# Security Agent

Specialist for configuring SAST, dependency scanning, container scanning, and secret detection across the uFawkesPipe platform.

## Context Files — Read First

| Priority | File                      | What You Learn                          |
| -------- | ------------------------- | --------------------------------------- |
| 1        | `AGENTS.md`               | Security expectations, credential rules |
| 2        | `docker-compose.yml`      | SonarQube, Dependency-Check services    |
| 3        | `.woodpecker.yml`         | Pipeline security stage configuration   |
| 4        | `.fawkespipe.yml.example` | Security stage configuration options    |
| 5        | `.github/workflows/*.yml` | CI security validation steps            |

## Tool Inventory

| Tool                   | Purpose                                | Config Location                           |
| ---------------------- | -------------------------------------- | ----------------------------------------- |
| SonarQube 10-community | SAST + quality gates                   | `docker-compose.yml`                      |
| Trivy                  | Filesystem, dependency, image scanning | `.woodpecker.yml` (step image)            |
| OWASP Dependency-Check | CVE database dependency audit          | `docker-compose.yml`                      |
| Hadolint               | Dockerfile linting                     | `.github/workflows/reusable-lint.yml`     |
| Gitleaks               | Secret detection                       | `.woodpecker.yml`, `.gitleaks.toml`       |
| detect-secrets         | Secret baseline                        | `.secrets.baseline`, pre-commit hooks     |

## Security Policies

### Vulnerability Severity Thresholds

| Scan Type              | Warn At               | Fail At              |
| ---------------------- | --------------------- | -------------------- |
| Trivy filesystem       | MEDIUM                | HIGH                 |
| Trivy image            | HIGH                  | CRITICAL             |
| OWASP Dependency-Check | MEDIUM                | CRITICAL (CVSS >= 7) |
| SonarQube              | All security hotspots | Quality gate failure |
| Gitleaks               | Any secret            | Any secret           |

### Credential Rules

- Never store credentials in pipeline YAML — use Woodpecker secret store or GitHub Actions secrets
- All secrets: 16+ characters, rotated every 90 days
- DockerHub token must be an access token, not password
- API tokens used for automation, not admin passwords

## Scan Configuration Standards

### Trivy

```bash
# Filesystem scan
trivy fs --severity HIGH,CRITICAL --format json --output report.json .

# Image scan
trivy image --severity CRITICAL --exit-code 1 ${IMAGE_TAG}

# Dependency scan
trivy fs --scanners vuln --severity HIGH,CRITICAL --format json .
```

### OWASP Dependency-Check

```bash
dependency-check --scan . --format JSON --format HTML \
  --out ./reports/ --failOnCVSS 7
```

### Gitleaks

```bash
gitleaks detect --source=. --report-format=json --report-path=artifacts/security/gitleaks.json --exit-code=1
```

## What You MAY Do

- Add new security tools to `docker-compose.yml` (pinned versions)
- Update severity thresholds in pipeline steps
- Add suppression files for known false positives
- Create security documentation in `docs/security/`

## What You MUST Ask Before

- Changing SonarQube version (affects quality gate compatibility)
- Adding a new scanning tool that requires persistent storage
- Modifying `failOnCVSS` defaults that affect all pipelines

## What You MUST NEVER

- Disable security scanning in pipeline defaults
- Set `fail_on` to `CRITICAL` or below for container images
- Commit suppression files without inline comments explaining each entry
- Store secrets in pipeline YAML files
