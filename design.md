# WP-007 — Design: Update QUICKSTART.md with v0.2 Prerequisites and Smoke Test

## 1. Impacted Components

| Component | File | Change |
|---|---|---|
| Quick Start Documentation | `QUICKSTART.md` | Full rewrite for v0.2 stack |
| Makefile targets | `Makefile` | Reference only (no changes) |
| Pipeline contract example | `examples/` | Reference only |

---

## 2. Document Structure Redesign

### 2.1 New Section Organization

```
# Quick Start Guide (v0.2)

## Prerequisites (updated)
## Installation (updated: make up / make up-suite)
## Configuration (updated: v0.2 .env.example)
## Service Access (updated: Woodpecker + SonarQube)
## Create Your First Pipeline (updated: .fawkespipe.yml)
## Smoke Test (new)
## Common Commands (updated)
## Troubleshooting (updated)
## Next Steps (updated)
```

### 2.2 Key Content Changes

| Old Section | New Content |
|---|---|
| Prerequisites | Add Woodpecker GitHub OAuth, CNB/pack, Docker Compose v2 |
| Installation | `make up` (standalone) / `make up-suite` (suite mode) |
| Configuration | All v0.2 env vars with descriptions |
| Service Access | Woodpecker (8000), SonarQube (9000) — no Jenkins |
| Pipeline Creation | `.fawkespipe.yml` contract + Woodpecker UI |
| Smoke Test | `make validate`, health checks, pipeline dry-run |
| Common Commands | v0.2 Makefile targets |

---

## 3. Detailed Content Specification

### 3.1 Prerequisites

```markdown
## Prerequisites

- **Docker 20.10+** — Container runtime
- **Docker Compose v2.0+** — `docker compose` (plugin, not standalone `docker-compose`)
- **4GB+ RAM** — For Woodpecker + SonarQube
- **GitHub OAuth App** — For Woodpecker authentication (Client ID + Secret)
- **DockerHub Account** — For image registry (username + access token)
- **DefectDojo Instance** (optional) — For security scan ingestion (API token)
- **`pack` CLI (optional)** — Cloud Native Buildpacks for local builds
- **uFawkesRes + uFawkesObs (optional)** — For suite mode (`make up-suite`)
```

### 3.2 Installation Modes

```markdown
## Installation

### Standalone Mode (make up)
Runs Woodpecker + SonarQube locally with SQLite/H2 storage.

```bash
git clone https://github.com/paruff/uFawkesPipe.git
cd uFawkesPipe
cp .env.example .env
# Edit .env with your credentials
make up
```

### Suite Mode (make up-suite)

Connects to uFawkesRes (PostgreSQL, Valkey, Traefik) and uFawkesObs (OTEL Collector).

```bash
# Terminal 1: Start dependencies
cd ../uFawkesRes && make up
cd ../uFawkesObs && make up

# Terminal 2: Start uFawkesPipe in suite mode
cd ../uFawkesPipe
make up-suite
```
```

### 3.3 Configuration (.env.example reference)

Document all variables with purpose and where to get values.

### 3.4 Service Access

| Service | URL | Credentials |
|---|---|---|
| Woodpecker CI | `http://localhost:8000` | GitHub OAuth |
| SonarQube | `http://localhost:9000` | admin / admin (change on first login) |

### 3.5 Pipeline Creation

```markdown
## Create Your First Pipeline

1. Add `.fawkespipe.yml` to your repository (see `.fawkespipe.yml.example`)
2. Push to GitHub
3. In Woodpecker UI: Add repository → Enable
4. Push code → Pipeline auto-triggers via GitHub webhook
```

### 3.6 Smoke Test

```markdown
## Smoke Test

Verify the installation is healthy:

```bash
# 1. Validate configuration and contracts
make validate

# 2. Run unit tests
make test

# 3. Check Woodpecker health
curl -sf http://localhost:8000/healthz && echo "Woodpecker OK"

# 4. Check SonarQube health
curl -sf http://localhost:9000/api/system/status | grep -q '"status":"UP"' && echo "SonarQube OK"

# 5. Verify pipeline contract
make validate-pipeline-contract
```

All commands should exit 0 with no errors.
```

### 3.7 Common Commands

Updated to v0.2 Makefile targets.

### 3.8 Troubleshooting

| Issue | Resolution |
|---|---|
| Woodpecker won't start | Check `make logs-woodpecker`, verify GitHub OAuth config |
| Port 8000 in use | `lsof -i :8000` |
| GitHub webhook fails | Verify `WOODPECKER_HOST` matches webhook URL |
| SonarQube won't start | Increase `vm.max_map_count`, check `make logs-sonar` |
| OTEL collector unreachable | Verify `OTEL_ENDPOINT`, check `make logs-otel` (suite mode) |

---

## 4. File Mapping

| Source | Lines | Action |
|---|---|---|
| `QUICKSTART.md` | 1-272 | Full rewrite |
| `.env.example` | 1-54 | Reference for config section |
| `compose.yaml` | — | Reference for services |
| `.fawkespipe.yml.example` | — | Reference for pipeline creation |

---

## 5. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Missing env var in docs | Medium | Cross-reference with `.env.example` |
| Broken links to examples | Low | Verify paths exist in repo |
| Outdated Makefile targets | Medium | Run `make help` to verify |
