# Changelog

All notable changes to uFawkesPipe will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Pre-commit hook validation for conventional commits
- Pre-push hook running all pre-commit checks
- `make validate-agents` target for agent/skill validation
- `make fix-and-commit` target for automated formatting + commit
- GitHub Actions issue templates (bug_report, feature_request)
- METRICS.md documentation for DORA metrics collection

### Changed

- Migrated agent/skill definitions from Jenkins to Woodpecker CI
- Updated observability-agent for OTEL/DORA integration with uFawkesObs
- Updated pipeline-library-agent for Woodpecker pipeline definitions
- Updated security-agent for Woodpecker secret handling
- Updated smoke-test-agent for Woodpecker health endpoints
- Updated workflow-agent for GitHub Actions standards
- Updated pipeline-contract skill for Woodpecker config loading

### Removed

- Legacy `shared/vars/*.groovy` Jenkins shared library files
- Legacy `jenkins/` directory (JCasC, plugin lists, seed jobs)
- Legacy `docker-compose.yml` (Jenkins-based stack)
- Legacy `k8s/` manifests (Jenkins-based, need update)

### Fixed

- Pre-push hook argument handling (`pass_filenames: false`)
- Agent/skill validation warnings (applies globs, context references)

## [0.3.0] - 2026-06-30

### Added

- Gitleaks secret scanning as hard gate in CI
- Woodpecker CI pipeline (`.woodpecker.yml`)
- Structured JSON logging for all pipeline steps
- DORA deployment event emission (`notify-obs` step)
- Suite mode with uFawkesRes + uFawkesObs integration
- SonarQube SAST integration
- Trivy vulnerability scanning (filesystem + image)
- OWASP Dependency-Check integration

### Changed

- CI/CD engine migrated from Jenkins to Woodpecker
- Pipeline contract renamed from `.deliveryd.yml` to `.fawkespipe.yml`
- Builder images updated to Paketo Buildpacks base
- Service labels standardized: `plane=ufawkespipe`, `managed-by=fawkes`

### Deprecated

- `.deliveryd.yml` contract filename (use `.fawkespipe.yml`)
- Jenkins-based pipeline definitions

## [0.2.0] - 2026-06-15

### Added

- Suite mode compose files (`compose.suite.yaml`)
- External network `fawkes-backbone-net` for uFawkesRes integration
- OTEL Collector integration for uFawkesObs
- Valkey cache service
- Authelia SSO integration
- Traefik ingress for suite mode

### Changed

- Architecture documentation updated
- Known limitations documented
- Golden path workflow documented

## [0.1.0] - 2026-06-01

### Added

- Initial uFawkesPipe release
- Jenkins-based CI/CD stack
- Pipeline contract specification
- Shared Groovy pipeline library
- Buildpack language packs (Java, Python, Node.js, Go)
- Docker Compose standalone deployment
- Basic security scanning (Trivy, Gitleaks)
