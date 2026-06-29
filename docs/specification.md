# uFawkesPipe — Specification v0.2
*CI/CD Plane of the Fawkes IDP Family*

**Status:** Draft — 2026-06-23
**Author:** Platform Engineering (solo contributor)
**Repo:** https://github.com/paruff/uFawkesPipe
**Supersedes:** README v0.1 (Jenkins framing, now removed)

---

## 1. Purpose and Scope

uFawkesPipe is the integration and delivery plane of the Fawkes IDP family. It provides a
**standardised pipeline contract** that polyglot application teams declare once (`.fawkespipe.yml`)
and the platform executes consistently across every push.

This specification covers the scope increase from the v0.1 baseline (Woodpecker + SonarQube +
Portainer + CNB) to the v0.2 target state that adds:

- A **DefectDojo security ingestion loop** for Gitleaks and Trivy findings
- A **standardised artifact directory contract** (`artifacts/security/`, `artifacts/coverage/`,
  `artifacts/tests/`) shared across all pipeline steps via Woodpecker workspace
- A **Gitleaks secrets-scan step** as a hard gate before any build step
- A **fawkes-net shared Docker network** so pipeline step containers can reach platform services
  by DNS name
- A **notify-obs step** that emits a structured deployment event to uFawkesObs (currently a
  stub; will carry pipeline duration, stage results, and SHA for DORA lead-time calculation)

**Out of scope for v0.2:**
- DefectDojo provisioning (assumed pre-existing on `fawkes-net`)
- Vault / Infisical integration (secrets still use Woodpecker native secrets store)
- Kubernetes promotion path (k8s/ manifests remain reference only)
- Fifth DORA metric (unconfirmed upstream; not encoded here)

---

## 2. Personas and JTBD

| Persona | Job To Be Done |
|---|---|
| **App developer** | Push code and get a pass/fail signal with actionable security findings in under 10 min |
| **Platform engineer** | Onboard a new repo to the pipeline in < 30 min with zero per-app pipeline YAML |
| **Security engineer** | See all secret and CVE findings aggregated in DefectDojo without touching CI config |
| **DORA practitioner** | Consume deployment frequency and lead-time events from uFawkesObs without manual tagging |

---

## 3. Functional Requirements

### 3.1 Pipeline Contract File (`.fawkespipe.yml`)

- Every application repository declares build metadata: `app.name`, `app.language`, `build.builder`
  (`cnb` or `docker`), `build.image.namespace`, and per-stage `enabled` flags.
- The platform `.woodpecker.yml` in uFawkesPipe reads no application-specific config at platform
  level; the contract file lives in the application repo.
- uFawkesPipe provides validated example contract files in `examples/` for: Java/Maven,
  Python/Flask, Node.js/Express, Go.

### 3.2 Pipeline Stages (ordered, all run in Woodpecker workspace)

| # | Stage | Image (pinned) | Artifact written | Hard gate? |
|---|---|---|---|---|
| 1 | `init` | `alpine:3.20` | Creates `artifacts/{security,coverage,tests}/` dirs | No |
| 2 | `secrets-scan` | `zricethezav/gitleaks:v8.18.2` | `artifacts/security/gitleaks.json` | **Yes** (`--exit-code 1`) |
| 3 | `lint-yaml` | `python:3.12-slim` | — | No (warn) |
| 4 | `lint-shell` | `koalaman/shellcheck-alpine:stable` | — | No (warn) |
| 5 | `unit-tests` | language-specific | `artifacts/tests/junit.xml`, `artifacts/coverage/coverage.xml` | Yes |
| 6 | `sast-sonarqube` | `sonarsource/sonar-scanner-cli:5.0` | SonarQube project analysis | Quality gate via SonarQube webhook |
| 7 | `vuln-scan-fs` | `aquasec/trivy:latest` | `artifacts/security/trivy-repo.json` | No (upload to Dojo) |
| 8 | `build` | `buildpacksio/pack:latest` or Docker | OCI image pushed to registry | Yes |
| 9 | `vuln-scan-image` | `aquasec/trivy:latest` | `artifacts/security/trivy-image.json` | No (upload to Dojo) |
| 10 | `upload-defectdojo` | `curlimages/curl:8.6.0` | — (POST to DefectDojo API v2) | No |
| 11 | `deploy-portainer` | `curlimages/curl:8.6.0` | — (POST to Portainer webhook) | Yes (on main branch only) |
| 12 | `notify-obs` | `curlimages/curl:8.6.0` | — (POST deployment event to uFawkesObs) | No |

**Note on Trivy tag:** `aquasec/trivy:latest` is intentionally unpinned for scanner images
so the CVE database stays current. This is an explicit, documented exception to the
pinned-image rule. All other images must be pinned to a digest or tag.

### 3.3 Artifact Directory Contract

All pipeline step containers share a single Woodpecker workspace directory. Steps write
artifacts to:

```
artifacts/
  security/
    gitleaks.json       # Gitleaks output (JSON format)
    trivy-repo.json     # Trivy filesystem scan (JSON format)
    trivy-image.json    # Trivy image scan (JSON format)
  coverage/
    coverage.xml        # Language-specific coverage (Cobertura XML preferred)
  tests/
    junit.xml           # JUnit XML (standard across all languages)
```

Steps downstream of a scanner must not assume the file exists if the producing step was
skipped; the `upload-defectdojo` step must check for file existence before POSTing.

### 3.4 DefectDojo Integration

- POST to `/api/v2/import-scan/` using `Authorization: Token $DOJO_API_TOKEN`
- `scan_type` values: `Gitleaks Scan` for `gitleaks.json`, `Trivy Scan` for Trivy outputs
- `engagement_name`: `CI-Engagement` (static)
- `project_name`: `${CI_REPO}` (Woodpecker built-in variable)
- `active=true`, `verified=false` for automated imports
- DefectDojo is assumed reachable at `http://defectdojo:8080` on `fawkes-net`

### 3.5 Portainer CD

- Deploy step fires on `branch: main` only
- Uses Woodpecker secret `portainer_webhook_stack_url`
- Single `POST` — no body required (Portainer webhook pulls and recreates the stack)

### 3.6 uFawkesObs Notification (stub for v0.2)

- Step runs after deploy on `branch: main`
- Payload (JSON): `{ "event": "deploy", "repo": "$CI_REPO", "sha": "$CI_COMMIT_SHA",
  "pipeline": "$CI_PIPELINE_NUMBER", "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)" }`
- Target URL: Woodpecker secret `obs_webhook_url`
- Non-blocking: failure does not fail the pipeline

### 3.7 Docker Network

- Woodpecker agent must be attached to `fawkes-net` (external network, pre-existing)
- `compose.yaml` declares `fawkes-net` as an external network
- Pipeline step containers inherit the agent's network, enabling DNS resolution of
  `defectdojo`, `sonarqube`, `portainer` by service name

### 3.8 Secrets

All secrets injected via Woodpecker native secrets (UI or CLI). Never in `.env` or `.woodpecker.yml`.

| Secret name | Used by stage | Description |
|---|---|---|
| `sonar_token` | `sast-sonarqube` | SonarQube user token |
| `defectdojo_api_token` | `upload-defectdojo` | DefectDojo API token |
| `portainer_webhook_stack_url` | `deploy-portainer` | Full Portainer webhook URL |
| `obs_webhook_url` | `notify-obs` | uFawkesObs event receiver URL |
| `registry_username` | `build` | OCI registry username |
| `registry_token` | `build` | OCI registry token |

---

## 4. Non-Functional Requirements

| Concern | Requirement |
|---|---|
| **Pipeline duration** | End-to-end (excl. first-run CVE DB download) < 10 min on a 4-core dev node |
| **Image pinning** | All non-scanner images pinned to tag; Trivy exception documented in `.woodpecker.yml` comment |
| **Secret hygiene** | No secrets in repo files; pre-commit Gitleaks hook enforces this locally |
| **Idempotency** | `make down && make up` must restore a clean working platform |
| **Single-node dev** | Full stack runs on Docker Compose with 4 GB RAM minimum |
| **Test coverage** | `pytest tests/` must pass on every PR; tests validate pipeline contract YAML structure |
| **Lint gates** | `yamllint` and `shellcheck` run on every push; failures are warnings, not hard gates (configurable) |

---

## 5. Acceptance Criteria

1. `make up` starts all 4 services (Woodpecker server + agent, SonarQube, Portainer) with no errors.
2. Pushing a commit with a planted secret causes `secrets-scan` to fail the pipeline with exit code 1.
3. A clean push on `main` produces: Trivy findings in DefectDojo, a Portainer stack redeploy,
   and a deployment event payload logged in the `notify-obs` step output.
4. `pytest tests/` passes with zero failures.
5. `yamllint compose.yaml .woodpecker.yml` reports zero errors.
6. All images in `compose.yaml` are pinned to a specific tag or digest (auditable via `grep image: compose.yaml`).

---

## 6. Open Questions (block implementation if unresolved)

| # | Question | Owner | Target |
|---|---|---|---|
| Q1 | Is DefectDojo deployed on `fawkes-net` before this work starts? | Platform engineer | Before issue WP-003 |
| Q2 | Which OCI registry is canonical for v0.2? DockerHub or self-hosted Harbor? | Platform engineer | Before issue WP-005 |
| Q3 | `notify-obs` payload schema — confirm field names with uFawkesObs team | Platform engineer | Before issue WP-006 |
