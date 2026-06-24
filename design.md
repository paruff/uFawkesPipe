# uFawkesPipe — Design v0.2
*CI/CD Plane of the Fawkes IDP Family*

**Status:** Draft — 2026-06-23
**Depends on:** specification.md v0.2

---

## 1. Component Map

```
┌──────────────────────────────────────────────────────────────────────┐
│  fawkes-net (external Docker bridge network)                         │
│                                                                      │
│  ┌─────────────────────┐   gRPC    ┌────────────────────────────┐   │
│  │  woodpecker-server  │◄─────────►│  woodpecker-agent          │   │
│  │  v3.15.0 :8000/:9000│           │  v3.15.0                   │   │
│  │  SQLite data volume │           │  mounts /var/run/docker.sock│   │
│  └─────────────────────┘           │  WOODPECKER_BACKEND=docker │   │
│                                    └────────────┬───────────────┘   │
│                                                 │ spawns ephemeral  │
│                                                 │ step containers   │
│  ┌──────────────────┐  ┌──────────────────┐    │                   │
│  │  sonarqube       │  │  portainer-ce    │    │                   │
│  │  lts-community   │  │  2.39.3          │    │                   │
│  │  :9001→9000      │  │  :9443 (HTTPS)   │    │                   │
│  └──────────────────┘  └──────────────────┘    │                   │
│                                                 │                   │
│  ┌──────────────────┐                           │                   │
│  │  defectdojo      │◄──────────────────────────┘                   │
│  │  (pre-existing)  │   upload-defectdojo step POSTs here           │
│  │  :8080           │                                               │
│  └──────────────────┘                                               │
└──────────────────────────────────────────────────────────────────────┘

External:
  GitHub       ──push webhook──►  woodpecker-server
  OCI Registry ◄──image push───   build step (pack or docker)
  uFawkesObs   ◄──POST event───   notify-obs step
```

---

## 2. Pipeline Step Design

Each step runs in an **ephemeral container** launched by the Woodpecker agent. The agent
mounts a shared workspace directory into every container; this is how artifacts flow between
steps without an external object store.

### 2.1 Workspace layout

```
/woodpecker/src/github.com/<org>/<repo>/   ← git checkout root (WOODPECKER_WORKSPACE)
  .woodpecker.yml
  .fawkespipe.yml
  artifacts/                               ← created by init step
    security/
    coverage/
    tests/
  <application source...>
```

### 2.2 Step-by-step design decisions

**`init`**
- Image: `alpine:3.20` (minimal, fast pull)
- Creates artifact dirs with `mkdir -p`; idempotent
- No secrets needed

**`secrets-scan` (hard gate)**
- Image: `zricethezav/gitleaks:v8.18.2` (pinned)
- `--exit-code 1` — pipeline stops here on any leak detection
- `--report-format json --report-path artifacts/security/gitleaks.json`
- `--exit-code 0` on the pre-commit hook; `--exit-code 1` only in CI to avoid developer workflow friction
- `.gitleaks.toml` already exists in repo — reuse it

**`lint-yaml` / `lint-shell`**
- Warnings only (`|| true` appended) — platform engineers accept that linting failures
  should not block a deploy in the current solo-contributor model; revisit at v0.3
- `yamllint` config: reuse existing `.yamllint`
- `shellcheck`: scans `scripts/*.sh validate.sh`

**`unit-tests`**
- Language-specific; the `.fawkespipe.yml` `stages.test.commands` block drives this
- Output must be JUnit XML at `artifacts/tests/junit.xml` for future uFawkesObs integration
- Coverage must be Cobertura XML at `artifacts/coverage/coverage.xml` for SonarQube

**`sast-sonarqube`**
- Image: `sonarsource/sonar-scanner-cli:5.0` (pinned)
- `-Dsonar.host.url=http://sonarqube:9000` — resolves via `fawkes-net` DNS
- `-Dsonar.python.coverage.reportPaths=artifacts/coverage/coverage.xml`
- SonarQube quality gate is checked asynchronously; pipeline does not block on it in v0.2
  (webhook-based quality gate enforcement is a v0.3 item)

**`vuln-scan-fs` and `vuln-scan-image`**
- Image: `aquasec/trivy:latest` (intentional; documented exception)
- `--format json` outputs to `artifacts/security/trivy-*.json`
- `--exit-code 0` — findings go to DefectDojo, not pipeline gate. Hard gate on image scan
  for CRITICAL severity is a v0.3 item (requires DefectDojo policy enforcement round-trip)
- `--no-progress` suppresses noisy output in CI logs

**`build`**
- Two paths: `pack build` (CNB) or `docker build`; controlled by `.fawkespipe.yml` `build.builder`
- CNB: `buildpacksio/pack:latest` with `paketobuildpacks/builder:base`
- Image tag pattern: `$REGISTRY_USERNAME/$APP_NAME:$CI_COMMIT_SHA_SHORT`
- Push to registry on `branch: main` only

**`upload-defectdojo`**
- Image: `curlimages/curl:8.6.0` (pinned)
- Shell `if [ -f artifacts/security/gitleaks.json ]; then curl ...; fi` pattern — defensive
- Three POSTs: gitleaks, trivy-repo, trivy-image
- `engagement_name=CI-Engagement` is static; DefectDojo auto-creates engagement if it does not exist
  (verify this assumption against your DefectDojo version before implementing)

**`deploy-portainer`**
- Image: `curlimages/curl:8.6.0`
- `when: branch: main` — never deploys on PRs
- Single `POST $PORTAINER_WEBHOOK_URL` — no body
- Portainer pulls latest image and recreates the stack atomically

**`notify-obs`**
- Image: `curlimages/curl:8.6.0`
- Payload: JSON with `event`, `repo`, `sha`, `pipeline`, `timestamp`
- `|| true` — never fails the pipeline
- Target URL from secret `obs_webhook_url`

---

## 3. compose.yaml Design Changes

Current `compose.yaml` (v0.1) declares a default network named `ufawkespipe_default`.
The Woodpecker agent is configured with `WOODPECKER_BACKEND_DOCKER_NETWORK=ufawkespipe_default`.

**v0.2 change:** Replace the implicit default network with an explicitly declared external
network `fawkes-net`. This allows DefectDojo (running in a separate compose stack or
standalone container) to be reachable by DNS name from pipeline step containers.

```yaml
# At bottom of compose.yaml:
networks:
  fawkes-net:
    external: true
    name: fawkes-net

# On woodpecker-agent service:
environment:
  - WOODPECKER_BACKEND_DOCKER_NETWORK=fawkes-net
networks:
  - fawkes-net

# On all other services:
networks:
  - fawkes-net
```

**Prerequisite:** `docker network create fawkes-net` must be run once before `make up`.
Document this in `QUICKSTART.md` and add a `make network` target to `Makefile`.

---

## 4. Secret Management Design

Woodpecker stores secrets encrypted in its SQLite database. Secrets are scoped to a
repository and injected as environment variables into the step container at runtime.

No secrets touch the filesystem or appear in logs. The `upload-defectdojo` step accesses
`$DOJO_API_TOKEN`; it is never echoed.

For v0.2, there is no Vault or Infisical integration. The `from_secret:` syntax in
`.woodpecker.yml` is the only secret delivery mechanism. This is acceptable for a
single-node dev environment. Production hardening is a v0.3 concern.

---

## 5. `.woodpecker.yml` Structure (v0.2 target)

```yaml
# uFawkesPipe CI/CD Pipeline — v0.2
# Secrets: sonar_token, defectdojo_api_token, portainer_webhook_stack_url,
#          obs_webhook_url, registry_username, registry_token

when:
  - event: [push, pull_request]

steps:

  - name: init
    image: alpine:3.20
    commands:
      - mkdir -p artifacts/security artifacts/coverage artifacts/tests

  - name: secrets-scan
    image: zricethezav/gitleaks:v8.18.2
    commands:
      - gitleaks detect --source=. --report-format=json
          --report-path=artifacts/security/gitleaks.json --exit-code=1

  - name: lint-yaml
    image: python:3.12-slim
    commands:
      - pip install yamllint --quiet
      - yamllint compose.yaml .woodpecker.yml .env.example || true

  - name: lint-shell
    image: koalaman/shellcheck-alpine:stable
    commands:
      - shellcheck scripts/*.sh validate.sh || true

  - name: unit-tests
    image: python:3.12-slim        # override per language in app repos
    commands:
      - pip install -r tests/requirements.txt --quiet
      - pytest tests/ -v --tb=short
          --junitxml=artifacts/tests/junit.xml
          --cov=. --cov-report=xml:artifacts/coverage/coverage.xml

  - name: sast-sonarqube
    image: sonarsource/sonar-scanner-cli:5.0
    environment:
      SONAR_TOKEN:
        from_secret: sonar_token
    commands:
      - sonar-scanner
          -Dsonar.host.url=http://sonarqube:9000
          -Dsonar.projectKey=${CI_REPO_NAME}
          -Dsonar.sources=.
          -Dsonar.python.coverage.reportPaths=artifacts/coverage/coverage.xml

  # aquasec/trivy:latest is intentionally unpinned — scanner images need
  # current CVE databases. This is a documented exception to pinned-image policy.
  - name: vuln-scan-fs
    image: aquasec/trivy:latest
    commands:
      - trivy fs --format json --output artifacts/security/trivy-repo.json
          --no-progress .

  - name: build
    image: buildpacksio/pack:latest
    environment:
      REGISTRY_USERNAME:
        from_secret: registry_username
      REGISTRY_TOKEN:
        from_secret: registry_token
    commands:
      - pack build ${REGISTRY_USERNAME}/${CI_REPO_NAME}:${CI_COMMIT_SHA:0:7}
          --builder paketobuildpacks/builder:base
          --publish
    when:
      - branch: main

  - name: vuln-scan-image
    image: aquasec/trivy:latest
    commands:
      - trivy image --format json
          --output artifacts/security/trivy-image.json --no-progress
          ${REGISTRY_USERNAME}/${CI_REPO_NAME}:${CI_COMMIT_SHA:0:7}
    when:
      - branch: main

  - name: upload-defectdojo
    image: curlimages/curl:8.6.0
    environment:
      DOJO_API_TOKEN:
        from_secret: defectdojo_api_token
    commands:
      - |
        for f in gitleaks trivy-repo trivy-image; do
          path="artifacts/security/${f}.json"
          [ -f "$path" ] || continue
          case "$f" in
            gitleaks)   scan_type="Gitleaks Scan" ;;
            trivy-repo) scan_type="Trivy Scan" ;;
            trivy-image) scan_type="Trivy Scan" ;;
          esac
          curl -sf -X POST "http://defectdojo:8080/api/v2/import-scan/" \
            -H "Authorization: Token $DOJO_API_TOKEN" \
            -F "active=true" -F "verified=false" \
            -F "scan_type=${scan_type}" \
            -F "engagement_name=CI-Engagement" \
            -F "product_name=${CI_REPO_NAME}" \
            -F "file=@${path}" || echo "WARN: DefectDojo upload failed for ${f}"
        done
    when:
      - branch: main

  - name: deploy-portainer
    image: curlimages/curl:8.6.0
    environment:
      PORTAINER_WEBHOOK_URL:
        from_secret: portainer_webhook_stack_url
    commands:
      - curl -sf -X POST "$PORTAINER_WEBHOOK_URL"
    when:
      - branch: main

  - name: notify-obs
    image: curlimages/curl:8.6.0
    environment:
      OBS_WEBHOOK_URL:
        from_secret: obs_webhook_url
    commands:
      - |
        curl -sf -X POST "$OBS_WEBHOOK_URL" \
          -H "Content-Type: application/json" \
          -d "{\"event\":\"deploy\",\"repo\":\"${CI_REPO}\",
               \"sha\":\"${CI_COMMIT_SHA}\",
               \"pipeline\":\"${CI_PIPELINE_NUMBER}\",
               \"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" \
          || echo "WARN: uFawkesObs notification failed (non-blocking)"
    when:
      - branch: main
```

---

## 6. Test Design

### 6.1 Existing tests (`tests/`)

The existing Python pytest suite validates `.fawkespipe.yml` contract structure (schema
validation, required fields, valid language values). These tests run in CI in the
`unit-tests` step. They must continue to pass.

### 6.2 New tests for v0.2

| Test file | What it validates |
|---|---|
| `tests/test_woodpecker_yml.py` | `.woodpecker.yml` parses as valid YAML; required step names present; `secrets-scan` appears before `build` |
| `tests/test_artifact_dirs.py` | `init` step commands create the three expected artifact directories |
| `tests/test_compose_network.py` | `compose.yaml` declares `fawkes-net`; Woodpecker agent has `WOODPECKER_BACKEND_DOCKER_NETWORK=fawkes-net` |

### 6.3 Integration smoke test (manual for v0.2)

Documented in `QUICKSTART.md` as a step-by-step checklist; not automated. Automation is
a v0.3 item.

---

## 7. File Change Summary

| File | Action | Notes |
|---|---|---|
| `.woodpecker.yml` | **Replace** | Full rewrite per section 5 above |
| `compose.yaml` | **Modify** | Add `fawkes-net` external network; update agent env var |
| `Makefile` | **Modify** | Add `network` target; update `up` to depend on it |
| `QUICKSTART.md` | **Modify** | Add `docker network create fawkes-net` prerequisite step |
| `.env.example` | **Modify** | Add `OBS_WEBHOOK_URL` placeholder |
| `tests/test_woodpecker_yml.py` | **Create** | New |
| `tests/test_artifact_dirs.py` | **Create** | New |
| `tests/test_compose_network.py` | **Create** | New |
| `docs/pipeline-contract.md` | **Create** | Explainer for DY-003 (existing open issue) |

---

## 8. Risks and Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| DefectDojo `import-scan` API signature differs from assumed | Medium | Verify against running DefectDojo instance before implementing WP-003; `|| echo WARN` prevents hard fail |
| `pack build --publish` requires Docker daemon access inside step container | High | Woodpecker agent mounts `/var/run/docker.sock`; confirmed in current compose.yaml |
| `fawkes-net` not created before `make up` | High | `make network` target creates it idempotently (`docker network create fawkes-net || true`) |
| Trivy image scan fails if build skipped on PR branch | Medium | `when: branch: main` on both build and image-scan steps; they share the same condition |
| SonarQube community edition limits on analysis frequency | Low | Single-node dev; not a concern at current scale |