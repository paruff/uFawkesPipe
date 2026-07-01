# WP-007 — Update QUICKSTART.md with v0.2 Prerequisites and Smoke Test

**Type:** docs / feat
**Depends on:** WP-001 (init), WP-004 (vuln-scan-fs), WP-005 (upload-defectdojo), WP-006 (notify-obs)
**Branch:** `feature/wp-007-quickstart-v02`

---

## 1. Problem

The current `QUICKSTART.md` documents the legacy Jenkins-based pipeline:
- References Jenkins at localhost:8080
- References legacy `docker-compose.yml` (not the v0.2 `compose.yaml`)
- Uses old `make init` / `make start` commands
- References Jenkinsfile for pipeline creation
- No v0.2 pipeline contract (`.fawkespipe.yml`) guidance
- No suite mode (`make up-suite`) documentation
- No smoke test verification steps

The v0.2 platform uses Woodpecker CI at localhost:8000, `compose.yaml` (Woodpecker + SonarQube), CNB/pack for builds, and the `.fawkespipe.yml` pipeline contract.

---

## 2. Requirements

### Functional

| # | Requirement | Rationale |
|---|---|---|
| F1 | Update prerequisites section for v0.2 stack (Docker, Docker Compose v2, `pack` CLI optional) | Accurate setup requirements |
| F2 | Document both standalone mode (`make up`) and suite mode (`make up-suite`) | Users need both options |
| F3 | Update environment configuration section with v0.2 `.env.example` variables | Correct credential guidance |
| F4 | Replace Jenkins references with Woodpecker CI (port 8000) | Reflect actual services |
| F5 | Document `.fawkespipe.yml` pipeline contract usage | v0.2 standard pipeline definition |
| F6 | Add smoke test section with verification commands | Validate installation works |
| F7 | Update common commands section for v0.2 Makefile targets | Accurate CLI reference |
| F8 | Update troubleshooting for v0.2 stack | Help users resolve issues |

### Non-Functional

| # | Requirement | Rationale |
|---|---|---|
| NF1 | Follow existing markdown style (headers, code blocks, tables) | Consistency with repo docs |
| NF2 | No hardcoded secrets — use `your_` placeholder convention | Security compliance |
| NF3 | Link to `compose.yaml` and `.woodpecker.yml` for reference | Developer discoverability |

---

## 3. Acceptance Criteria

1. Prerequisites section lists: Docker 20.10+, Docker Compose v2.0+, 4GB+ RAM, GitHub OAuth app for Woodpecker, `pack` CLI (optional for CNB builds)
2. Installation documents both `make up` (standalone) and `make up-suite` (connects to uFawkesRes/uFawkesObs)
3. Environment configuration references all v0.2 `.env.example` variables: WOODPECKER_GITHUB_CLIENT, WOODPECKER_GITHUB_SECRET, WOODPECKER_AGENT_SECRET, WOODPECKER_HOST, SONARQUBE_ADMIN_PASSWORD, REGISTRY_USERNAME, REGISTRY_TOKEN, DOJO_API_TOKEN, POSTGRES_PASSWORD, WOODPECKER_METRICS_TOKEN, UFAWKES_ENVIRONMENT, OTEL_ENDPOINT, OTEL_HEADERS
4. Service access: Woodpecker at `http://localhost:8000`, SonarQube at `http://localhost:9000`
5. Pipeline creation uses `.fawkespipe.yml` contract (not Jenkinsfile)
5. Smoke test section with: `make validate`, `make test`, `curl` health checks for Woodpecker and SonarQube
6. Common commands updated: `make up`, `make up-suite`, `make down`, `make logs`, `make status`, `make validate`, `make test`
7. Troubleshooting covers: Woodpecker won't start, port conflicts, GitHub OAuth issues, OTEL collector connectivity
8. All markdown passes `markdownlint` and `pre-commit run --all-files`
9. Links to `compose.yaml`, `.woodpecker.yml`, `.fawkespipe.yml.example` are valid

---

## 4. Dependencies

- **WP-001** (init): Artifact directories must exist for validation
- **WP-004** (vuln-scan-fs): Smoke test may run pipeline validation
- **WP-005** (upload-defectdojo): Security scan references in docs
- **WP-006** (notify-obs): Observability references in docs

---

## 5. Out of Scope

- Full `README.md` rewrite (separate effort)
- `docs/ARCHITECTURE.md` updates (separate effort)
- `docs/KNOWN_LIMITATIONS.md` updates (separate effort)
- Migration guide for Jenkins → Woodpecker (separate effort)
