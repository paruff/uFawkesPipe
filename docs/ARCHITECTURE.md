# uFawkesPipe — Architecture

> CI/CD Plane of the Fawkes IDP Family
> **Status:** Current (Woodpecker-based) — Legacy Jenkins path documented in §9

---

## 1. System Overview

uFawkesPipe is a **CI/CD platform** for polyglot application development. It provides automated build, test, security scanning, and deployment capabilities via **Woodpecker CI** + **Docker Compose**.

**Key design principles:**
- **Pipeline contract** — Application teams declare their pipeline once in `.fawkespipe.yml`; the platform executes it consistently across every push.
- **Polyglot by default** — CNB (Cloud Native Buildpacks) handles most languages; Docker build is also supported.
- **Security-first** — Gitleaks secrets scanning, Trivy vulnerability scanning, SonarQube SAST.
- **Single-node dev** — Full stack runs on Docker Compose; K8s promotion path is documented but secondary.
- **DORA-ready** — Pipeline emits structured deployment events for lead-time and deployment frequency tracking.

---

## 2. Component Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ufawkespipe_default (Docker bridge network)                            │
│                                                                         │
│  ┌──────────────────────┐   gRPC :9000  ┌──────────────────────────┐   │
│  │  woodpecker-server   │◄─────────────►│  woodpecker-agent        │   │
│  │  :8000 (UI)          │               │  mounts /var/run/docker… │   │
│  │  SQLite data volume  │               │  WOODPECKER_BACKEND=docker│  │
│  └──────────────────────┘               └───────────┬──────────────┘   │
│                                                      │ spawns           │
│                                                      │ ephemeral step   │
│                                                      │ containers       │
│  ┌──────────────────────┐  ┌──────────────────────┐  │                  │
│  │  sonarqube           │  │  portainer            │  │                  │
│  │  lts-community       │  │  2.39.3               │  │                  │
│  │  :9001→:9000         │  │  :9443 (HTTPS UI)     │  │                  │
│  │                      │  │  :9002→:8000 (edge)   │  │                  │
│  └──────────────────────┘  └──────────────────────┘  │                  │
│                                                      │                  │
│  GitHub ──push webhook──► woodpecker-server          │                  │
│  OCI Registry ◄──image push── build step             │                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Services

| Service | Image | Port(s) | Role |
| ------- | ----- | ------- | ---- |
| **woodpecker-server** | `woodpeckerci/woodpecker-server:v3.15.0` | `8000` (UI), `9000` (gRPC) | CI/CD orchestration, webhook receiver, pipeline state |
| **woodpecker-agent** | `woodpeckerci/woodpecker-agent:v3.15.0` | — | Pipeline step execution via Docker-in-Docker |
| **sonarqube** | `sonarqube:lts-community` | `9001→:9000` | SAST code quality analysis |
| **portainer** | `portainer/portainer-ce:2.39.3` | `9443` (HTTPS), `9002` (edge) | Container management, CD via webhook stacks |

### Labels

Every service carries standard Fawkes labels:

```yaml
labels:
  - "plane=ufawkespipe"
  - "component=<ci-server|ci-agent|sast|cd-engine>"
  - "managed-by=fawkes"
```

---

## 3. Pipeline Architecture

### 3.1 Pipeline Contract (`.fawkespipe.yml`)

The pipeline contract is the interface between application teams and the platform. It lives in the **application repository** (not in uFawkesPipe).

```yaml
# .fawkespipe.yml (in app repo)
app:
  name: my-app                # required
  type: service               # service | library | cli | frontend
  language: java              # primary language
  version: 1.0.0

build:
  builder: cnb                # cnb | docker | custom
  cnb:
    builder: paketobuildpacks/builder:base
  image:
    registry: docker.io
    namespace: ${DOCKERHUB_USERNAME}
    tags:
      - "${GIT_COMMIT_SHORT}"
      - "latest"

stages:
  lint:
    enabled: true
    commands: ...
  test:
    enabled: true
    coverage:
      enabled: true
      threshold: 80
  sast:
    enabled: true
  ...
```

### 3.2 Platform Pipeline (`.woodpecker.yml`)

uFawkesPipe's own CI pipeline runs **on every push and pull request**:

```
lint-yaml → lint-shell → validate-pipeline-contract → security-scan (main only) → notify-obs (main only)
```

| Step | Image | When | Hard gate? |
| ---- | ----- | ---- | ---------- |
| `lint-yaml` | `python:3.12-slim` | always | No (warn) |
| `lint-shell` | `koalaman/shellcheck-alpine:stable` | always | No (warn) |
| `validate-pipeline-contract` | `python:3.12-slim` | always | Yes |
| `security-scan` | `aquasec/trivy:latest` | push → main only | Yes (`--exit-code 1` for HIGH,CRITICAL) |
| `notify-obs` | `curlimages/curl:7.88.1` | push → main only | No (OTLP event to uFawkesObs, graceful fallback) |

**Image pinning policy:** All non-scanner images pinned to a specific tag. Trivy (`aquasec/trivy:latest`) is the documented exception — scanner images need current CVE databases.

### 3.3 Artifact Directory Contract

Pipeline steps share a Woodpecker workspace (`/woodpecker/src/github.com/<org>/<repo>/`). Artifacts go to:

```
artifacts/
  security/
    gitleaks.json       # Gitleaks output (when integrated)
    trivy-repo.json     # Trivy filesystem scan
    trivy-image.json    # Trivy image scan
  coverage/
    coverage.xml        # Cobertura XML
  tests/
    junit.xml           # JUnit XML
```

---

## 4. Network Architecture

All services run on `ufawkespipe_default` (auto-created Docker bridge network).

- **Woodpecker server-to-agent**: gRPC on port 9000
- **Woodpecker agent-to-step containers**: Docker socket mounted at `/var/run/docker.sock`
- **External ingress**:
  - GitHub webhooks → woodpecker-server :8000
  - User access: Woodpecker UI (:8000), SonarQube (:9001), Portainer (:9443)

---

## 5. Data Flow

### Push → Pipeline

```
1. GitHub push webhook → woodpecker-server :8000
2. woodpecker-server assigns pipeline → woodpecker-agent (gRPC)
3. woodpecker-agent clones repo into workspace
4. Agent spawns sequential step containers (Docker-in-Docker)
5. Each step reads .woodpecker.yml and .fawkespipe.yml
6. Artifacts passed between steps via shared workspace
7. Pipeline result → woodpecker-server → GitHub commit status
```

### Deployment

```
1. Push to main → deploy-portainer step triggered (.woodpecker.yml)
2. curl POST to Portainer webhook URL (from secret PORTAINER_WEBHOOK_URL)
3. Portainer pulls latest image, recreates stack atomically
```

### Security Pipeline

```
1. trivy fs scans filesystem for HIGH/CRITICAL vulnerabilities
2. SonarQube is available for SAST (via sonarqube:9000 on the network)
3. Results viewable in SonarQube UI (:9001) or Portainer (:9443)
```

---

## 6. Secrets Architecture

Secrets are stored in **Woodpecker native secrets store** (encrypted in SQLite).

| Secret | Used By | Description |
| ------ | ------- | ----------- |
| `WOODPECKER_GITHUB_CLIENT` | woodpecker-server | GitHub OAuth client ID |
| `WOODPECKER_GITHUB_SECRET` | woodpecker-server | GitHub OAuth client secret |
| `WOODPECKER_AGENT_SECRET` | woodpecker-server + agent | Agent-to-server auth |
| `SONARQUBE_ADMIN_PASSWORD` | sonarqube | Admin password (set via .env) |

**Rules:**
- No secrets in repo files (`.env` is in `.gitignore`)
- Pre-commit Gitleaks hook enforces locally
- `from_secret:` syntax in `.woodpecker.yml` is the only delivery mechanism
- No Vault / Infisical integration (future scope)

---

## 7. Integration Points

| System | Protocol | Port | Direction | Purpose |
| ------ | -------- | ---- | --------- | ------- |
| GitHub | Webhook (HTTP POST) | 8000 | → uFawkesPipe | Trigger pipelines |
| OCI Registry | Docker push | — | ← uFawkesPipe | Image storage |
| **uFawkesObs** (suite mode) | OTLP gRPC | 4317 | → OBS | Traces + metrics + logs |
| **uFawkesObs** (suite mode) | OTLP HTTP | 4318 | → OBS | Deployment events |
| **uFawkesObs** (suite mode) | Prometheus scrape | 8000/metrics | ← OBS | Pipeline metrics |
| **uFawkesRes** (suite mode) | PostgreSQL | 5432 | ⇄ Res | Shared database |
| **uFawkesRes** (suite mode) | Traefik ingress | 80 | → Pipe | Reverse proxy + SSO |
| Developer tooling | Pipeline events | — | → developerd | Status read (future) |

---

## 8. Kubernetes Promotion Path

uFawkesPipe can run on Kubernetes. See `docs/kubernetes-promotion.md` for the full migration guide.

**Current K8s manifests** in `k8s/`:
- `jenkins-deployment.yaml` — Jenkins StatefulSet
- `jenkins-service.yaml` — Service
- `jenkins-ingress.yaml` — Ingress
- `jenkins-pvc.yaml` — PersistentVolumeClaim (for Jenkins home)
- `jenkins-rbac.yaml` — ServiceAccount + RBAC

**Note:** The K8s manifests still reference the Jenkins-based architecture. They need updating when the promotion path is revalidated against the Woodpecker-based stack.

---

## 12. Suite Mode Architecture

uFawkesPipe supports two deployment modes:

| Mode | Command | Dependencies | Use case |
| ---- | ------- | ------------ | -------- |
| **Standalone** | `make up` | None | Local dev, isolated testing |
| **Suite** | `make up-suite` | uFawkesRes + uFawkesObs running | Full IDP integration |

### 12.1 Standalone Mode (default)

The default mode — no external dependencies. All services use embedded/SQLite storage and a private Docker network. See §2 for the component map.

### 12.2 Suite Mode

Suite mode extends standalone mode via `compose.suite.yaml` (Docker Compose override):

```
compose.yaml + compose.suite.yaml → make up-suite
```

**Network topology in suite mode:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  fawkes-backbone-net (ufawkes-resources_fawkes-backbone-net)             │
│  Created by: uFawkesRes                                                  │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ woodpecker-  │  │  sonarqube   │  │  portainer   │                  │
│  │ server       │  │              │  │              │                  │
│  │ PostgreSQL   │  │  PostgreSQL  │  │              │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│         │                                                                │
│         │  Also on fawkes-backbone-net (from uFawkesRes):                │
│         │  - fawkes-postgres:5432  (shared PostgreSQL)                    │
│         │  - fawkes-cache:6379     (shared Valkey)                        │
│         │  - fawkes-ingress:80     (Traefik)                              │
│         │  - fawkes-sso:9091       (Authelia SSO)                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  observability-lab                                                       │
│  Created by: uFawkesObs                                                  │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ woodpecker-  │  │ woodpecker-  │  │  portainer   │                  │
│  │ server       │  │ agent        │  │              │                  │
│  │ OTEL exports │  │              │  │              │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│         │                                                                │
│         │  Also on observability-lab (from uFawkesObs):                  │
│         │  - otel-collector:4317   (OTLP gRPC)                           │
│         │  - otel-collector:4318   (OTLP HTTP)                           │
│         │  - tempo:4317           (traces)                               │
│         │  - loki:3100            (logs)                                 │
│         │  - prometheus:9090      (metrics)                              │
│         │  - grafana:3000         (dashboards)                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### 12.3 What Changes in Suite Mode

| Component | Standalone | Suite |
| --------- | ---------- | ----- |
| **Woodpecker DB** | SQLite (local volume) | PostgreSQL on fawkes-postgres:5432 |
| **SonarQube DB** | Embedded H2 | PostgreSQL on fawkes-postgres:5432 |
| **OTEL exporter** | None | gRPC → otel-collector:4317 |
| **Metrics** | None (no scrape target) | Prometheus scrape (with WOODPECKER_METRICS_TOKEN) |
| **Logs** | Docker json-file (local) | Alloy scrapes → Loki |
| **Events** | `notify-obs` writes to stdout | `notify-obs` POSTs OTLP to otel-collector:4318 + stdout |
| **Ingress** | Direct port access | Traefik on fawkes-backbone-net |
| **Auth** | None | Authelia SSO via fawkes-sso |

### 12.4 Telemetry Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│  uFawkesPipe                                        uFawkesObs   │
│                                                                   │
│  ┌──────────────────┐      OTLP gRPC (traces+metrics+logs)        │
│  │ woodpecker-server├─────────────────────────────────►otel-     │
│  │                  │                                collector  │
│  │ /metrics endpoint│◄──────── Prometheus scrape ────┤           │
│  └──────────────────┘                                │ :4317     │
│                                                      │ :4318     │
│  ┌──────────────────┐      OTLP HTTP (events)        │           │
│  │  notify-obs step ├─────────────────────────────────►           │
│  │  (ephemeral)     │                                └─────┬─────┘
│  └──────────────────┘                                       │
│                                                             │
│  ┌──────────────────┐       Docker logs (structured JSON)   │
│  │  All steps       ├─────────────────────────────────►Alloy───►Loki
│  │  (stdout)        │                                scrapes   │
│  └──────────────────┘                                └──►Tempo │
│                                                             └──►Grafana
└───────────────────────────────────────────────────────────────────┘
```

**Telemetry signals emitted:**

| Signal | Source | Protocol | Destination | Status |
| ------ | ------ | -------- | ----------- | ------ |
| **Metrics** | Woodpecker server `/metrics` | Prometheus scrape (HTTP) | Prometheus :9090 | ✅ Configured |
| **Traces** | Woodpecker server | OTLP gRPC → :4317 | Tempo | ✅ Configured |
| **Logs (service)** | Docker container logs | Docker json-file → Alloy scrape | Loki | ✅ Auto (Alloy discovers all containers) |
| **Logs (pipeline)** | Pipeline steps (stdout) | Structured JSON → Docker logs → Alloy scrape | Loki | ✅ All steps emit JSON |
| **Events** | `notify-obs` step | OTLP HTTP → :4318 | Loki via collector | ✅ Active (with graceful fallback) |

**Note on traces:** Woodpecker server natively supports OTEL export of its own traces (request handling, pipeline scheduling). Per-pipeline-step traces are not yet available — that requires Woodpecker-native pipeline span emission (future). Pipeline events provide the deployment signal for DORA lead-time calculation in the interim.

---

## 9. Legacy Architecture (Jenkins-based)

The current stack uses **Woodpecker CI** as its pipeline engine. The previous architecture used **Jenkins**. The deprecated `docker-compose.yml` and `k8s/` manifests still reference Jenkins.

### Deprecated Jenkins stack

```
docker-compose.yml (deprecated):
  - jenkins          (CI/CD orchestration)
  - sonarqube        (SAST) + sonarqube-db (PostgreSQL)
  - dependency-check (OWASP dependency scanning)
  - pack-cli         (CNB builds)
  - (optional) nexus (artifact repository)
```

### Migration status

| Component | Old (Jenkins) | New (Woodpecker) | Status |
| --------- | ------------- | ----------------- | ------ |
| CI server | Jenkins | Woodpecker Server | ✅ Done |
| Pipeline exec | Jenkins agents | Woodpecker Agent | ✅ Done |
| SAST | SonarQube | SonarQube | ✅ Same |
| CD | Jenkins pipeline | Portainer webhook | ✅ Done |
| Buildpacks | Pack CLI (on-demand) | CNB via .fawkespipe.yml | ✅ Done |
| Dependency scan | OWASP Dependency-Check | Trivy fs scan | ✅ Done |
| Artifact repo | Nexus (commented out) | OCI registry | ✅ Done |
| Shared lib | `shared/` (Jenkins vars/) | `.fawkespipe.yml` contract | 🔄 Partial |
| K8s manifests | Jenkins-based | Needs update | ❌ Pending |

### Why the migration happened

1. **Simpler configuration** — Woodpecker uses a single `.woodpecker.yml` file vs Jenkins' JCasC + plugin matrix
2. **Lighter footprint** — Woodpecker is lighter than Jenkins (SQLite vs no DB for basic use)
3. **Docker-native** — Woodpecker agent uses Docker-in-Docker natively; Jenkins needed Docker Pipeline plugin
4. **Pipeline contract** — `.fawkespipe.yml` provides a cleaner separation between platform and app config

---

## 10. Test Architecture

### Test Tiers

| Tier | Command | Location | Requires |
| ---- | ------- | -------- | -------- |
| Unit | `make test-unit` | `tests/unit/` | pytest |
| Integration | `make test-integration` | `tests/integration/` | Docker |
| Smoke | `make test-smoke` | `tests/smoke/` | Running stack |
| Acceptance | `make test-acceptance` | `tests/acceptance/` | Running stack |

### Current test coverage (`tests/unit/`)

Tests validate:
- `.fawkespipe.yml` contract structure (schema validation, required fields, valid language values)
- `.woodpecker.yml` step ordering and required stages
- Artifact directory initialization

---

## 11. File Reference Map

| Path | Language | Purpose |
| ---- | -------- | ------- |
| `compose.yaml` | YAML | Service orchestration — standalone mode (Woodpecker, SonarQube, Portainer) |
| `compose.suite.yaml` | YAML | Suite mode overlay — connects to uFawkesRes + uFawkesObs |
| `.woodpecker.yml` | YAML | Pipeline definition for uFawkesPipe's own CI |
| `.fawkespipe.yml.example` | YAML | Pipeline contract template for app teams |
| `Makefile` | Make | `make up`, `make validate`, `make test-*` targets |
| `validate.sh` | Bash | Pre-flight validation (Docker, YAML, files, `.env`) |
| `tests/` | Python | pytest suite for contract + pipeline validation |
| `scripts/` | Bash | Git hooks (pre-commit, commit-msg) |
| `examples/` | YAML | `.fawkespipe.yml` examples for Java, Python, Node.js, Go |
| `k8s/` | YAML | K8s manifests (Jenkins-based, needs updating) |
| `docs/` | Markdown | Documentation |
| `docker-compose.yml` | YAML | **Deprecated** — legacy Jenkins stack, retained for reference |
| `shared/` | — | Shared workspace for Jenkins pipeline artifacts (legacy) |
