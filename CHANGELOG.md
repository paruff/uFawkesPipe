# Changelog

All notable changes to uFawkesPipe will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.3.0-beta.1...v1.4.0-beta.1) (2026-09-02)


### Added

* **ci:** add release-please, pin opencode-ai off [@latest](https://github.com/latest) ([#78](https://github.com/paruff/uFawkesPipe/issues/78)) ([b3c504f](https://github.com/paruff/uFawkesPipe/commit/b3c504fd90454821e02138242deaeeb5425ba12e))
* **docs:** host shared DORA event contracts, sourced from uFawkesObs ([#69](https://github.com/paruff/uFawkesPipe/issues/69)) ([d399061](https://github.com/paruff/uFawkesPipe/commit/d39906149a9971c89e6da4b083c2ca827d7c9051))


### Fixed

* **ci:** allow external_directory writes for opencode ([#73](https://github.com/paruff/uFawkesPipe/issues/73)) ([32326eb](https://github.com/paruff/uFawkesPipe/commit/32326eb059dac2c0431853cb8cc0619986082037))
* **dora:** send deployment events to uFawkesObs REST /event endpoint ([#70](https://github.com/paruff/uFawkesPipe/issues/70)) ([9a9b8b8](https://github.com/paruff/uFawkesPipe/commit/9a9b8b8e2fdb3423ecb8fc1dd1b8e9c9465e2298))


### Docs

* document never-swallow-exceptions principle in coding standards ([#72](https://github.com/paruff/uFawkesPipe/issues/72)) ([6fc8ab0](https://github.com/paruff/uFawkesPipe/commit/6fc8ab0109663f55b21ecbf849902a0e6ca427dc))
* **dora:** document OTLP telemetry contract, add commit-format guidance ([#71](https://github.com/paruff/uFawkesPipe/issues/71)) ([7f5a090](https://github.com/paruff/uFawkesPipe/commit/7f5a09052360b0579646dbc63d5aca59aefe386e))


### Chores

* **deps:** bump actions/checkout from 4 to 7 ([#74](https://github.com/paruff/uFawkesPipe/issues/74)) ([4c9e618](https://github.com/paruff/uFawkesPipe/commit/4c9e618ded73c57fbe4d7e3c4fa0c71ffacb59b9))
* **deps:** bump actions/setup-node from 4 to 7 ([#75](https://github.com/paruff/uFawkesPipe/issues/75)) ([62fcf53](https://github.com/paruff/uFawkesPipe/commit/62fcf531a21a22c91d9bc68244d52fcdaad59a37))
* **deps:** bump hadolint/hadolint-action from 3.4.0 to 3.5.0 ([#77](https://github.com/paruff/uFawkesPipe/issues/77)) ([2a2e153](https://github.com/paruff/uFawkesPipe/commit/2a2e1534d1136cc13c0573657e484b9ba08a0dbf))
* **deps:** bump trufflesecurity/trufflehog from 3.97.0 to 3.97.1 ([#76](https://github.com/paruff/uFawkesPipe/issues/76)) ([fe0fcad](https://github.com/paruff/uFawkesPipe/commit/fe0fcad085ad19c1e50f3bacd2f3cddccb33169e))

## [1.3.0-beta.1] - 2026-08-10

### Added

- `.fawkespipe.yml` → `.woodpecker.yml` pipeline contract generator (`make generate-pipeline` / `make check-pipeline`), resolving beta blocker B-1 (PIPE-009, #64)
- GitOps lifecycle gates (#55)
- Pre-commit hook validation for conventional commits
- Pre-push hook running all pre-commit checks
- `make validate-agents` target for agent/skill validation
- `make fix-and-commit` target for automated formatting + commit
- GitHub Actions issue templates (bug_report, feature_request)
- METRICS.md documentation for DORA metrics collection
- `docs/BETA_RELEASE_PLAN.md` beta-readiness audit and action plan (#63)

### Changed

- Migrated remaining agent/skill definitions and scripts from Jenkins to Woodpecker CI (#60)
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
- Legacy `k8s/` manifests (Jenkins-based, superseded by `compose.yaml` + `.woodpecker.yml`)

### Fixed

- Pre-push hook argument handling (`pass_filenames: false`)
- Agent/skill validation warnings (applies globs, context references)
- Preflight job no longer fails when the PR-size comment lacks `issues:write` permission (#59)

## [1.2.0] - 2026-07-18

### Added

- `policy-check` pipeline step for Rego policy validation (#49)
- `generate-sbom` and `sign-image` supply-chain pipeline steps (#48)
- `make health` / `make health-suite` targets for container health status (#44)
- `reusable-main-ci-guard` and `reusable-rollback` GitHub Actions workflows (#54)

### Changed

- `allow-latest` input added for documented `:latest` image-tag exceptions (#43)

## [1.1.1] - 2026-07-02

### Added

- Automated golden-path acceptance test suite, AC-01–AC-14 (#42)
- `validate-agents` Woodpecker CI step (PIPE-008, #41)
- Staged pipeline restructure with consolidated test suites (WP-009, #37)
- `notify-obs` deployment event step (WP-006, #34)
- `upload-defectdojo` telemetry collector step (WP-005, #33)
- `vuln-scan-fs` / `vuln-scan-image` Trivy steps (WP-004, #31)
- `secrets-scan` (Gitleaks) hard-gate step (WP-003, #27)
- `fawkes-net` external network for suite mode (WP-002, #25)
- `ARCHITECTURE.md`, `KNOWN_LIMITATIONS.md`, `GOLDEN_PATH.md`, `MODEL_POLICY.md`, plus suite-mode compose (#24)
- uFawkesPipe v0.2 specification document (#23)

### Changed

- Agents/skills migrated from Jenkins to Woodpecker CI, plus Score integration (#30)
- README and `QUICKSTART.md` updated for the v0.2 Woodpecker CI stack (#35, #36)

### Fixed

- Pre-push guardrail added; pre-commit runs read-only in CI; flaky SBOM pre-check removed (#28, #29, #32)

## [1.1.0] - 2026-06-27

### Fixed

- Coverage-threshold enforcement and e2e test defaults added (#21)

## [1.0.0] - 2026-06-27

### Added

- GitHub Actions CI workflow for the repo itself (DY-002)

### Changed

- Renamed `deliveryd` → `uFawkesPipe` across identity, metadata, platform config, and K8s manifests
- Renamed pipeline contract file `.deliveryd.yml` → `.fawkespipe.yml`

### Fixed

- CI workflow failures, yamllint failures, invalid shellcheck action, Node.js 24 deprecation warning

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
