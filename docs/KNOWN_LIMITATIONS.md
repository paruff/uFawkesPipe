# Known Limitations — uFawkesPipe

> Agents should read this before building to avoid making these worse.
> This is a living document — add entries as you discover them.

---

## Current Limitations

### Architecture & Documentation

| # | Limitation | Impact | Mitigation |
| - | ---------- | ------ | ---------- |
| L-001 | ~~`docs/ARCHITECTURE.md` documents the Woodpecker-based stack, but `k8s/` manifests and `docker-compose.yml` still reference the legacy Jenkins architecture~~ | **RESOLVED:** Legacy Jenkins stack (`docker-compose.yml`, `k8s/`, `jenkins/`, `Jenkinsfile`) fully removed; only `compose.yaml` + `.woodpecker.yml` define the stack | `compose.yaml` and `.woodpecker.yml` are the source of truth; see `docs/history/jenkins-migration.md` |
| L-002 | ~~No `docs/GOLDEN_PATH.md` exists~~ | **RESOLVED:** `docs/GOLDEN_PATH.md` exists and documents the canonical "idea → deploy" workflow | Read it for the full sequence; deviations require documented justification per that doc |
| L-003 | ~~No `docs/MODEL_POLICY.md` exists~~ | **RESOLVED:** `docs/MODEL_POLICY.md` exists | Read it for model selection and cost tracking |
| L-004 | `.github/copilot-instructions.md` and `.github/instructions/` don't exist | **RESOLVED:** Agents use `AGENTS.md` as the single source of truth; Copilot instructions are not required for agent operation | Agents proceed with AGENTS.md as the primary instruction source; no Copilot-specific config needed |

### Pipeline & CI

| # | Limitation | Impact | Mitigation |
| - | ---------- | ------ | ---------- |
| L-005 | ~~The pipeline contract (`.fawkespipe.yml.example`) is aspirational — `.woodpecker.yml` doesn't actually read it at runtime~~ | **RESOLVED:** `scripts/generate_woodpecker_yml.py` translates `.fawkespipe.yml` into executable `.woodpecker.yml` via `make generate-pipeline`; `kubernetes:` and `notifications:` fields are parsed but not yet wired to pipeline steps (future scope) | See `docs/pipeline-contract.md` and `examples/fawkespipe-contract-migration/` |
| L-006 | `notify-obs` uses non-blocking POST (falls back on failure) | **RESOLVED:** Emits structured JSON deployment event to OTEL collector with graceful `dora_warn` fallback when endpoint unavailable | Fixed in v2.0; events logged to stdout for local debugging |
| L-007 | ~~No automated integration or E2E tests exist — only unit tests~~ | **RESOLVED:** Integration, smoke, and acceptance tests exist; acceptance suite verifies full golden path | Run with `make test-unit`, `make test-integration`, `make test-smoke`, `make test-acceptance` |
| L-008 | ~~`security-scan` runs only on `push → main`, not on PRs~~ | **RESOLVED:** `vuln-scan-fs` runs on all branches; `vuln-scan-image` runs on main only | File system scan runs on every push and PR |
| L-009 | ~~No Gitleaks secrets scan in the Woodpecker pipeline~~ | **RESOLVED:** `secrets-scan` step added as hard gate (`--exit-code 1`) | Runs on every push and pull request |

### Stack & Infrastructure

| # | Limitation | Impact | Mitigation |
| - | ---------- | ------ | ---------- |
| L-010 | Woodpecker uses SQLite (single-file database) | **RESOLVED:** Acceptable for single-node dev; PostgreSQL migration planned for suite mode via uFawkesRes shared Postgres | SQLite is sufficient for pre-alpha; migrate when scaling |
| L-011 | SonarQube uses embedded H2 database (no PostgreSQL container in `compose.yaml`) | **RESOLVED:** Acceptable for dev; H2 data loss risk mitigated by ephemeral scan-only usage | PostgreSQL migration planned for suite mode |
| L-012 | Trivy image uses `latest` tag (intentional, documented exception) | **RESOLVED:** Accepted trade-off for up-to-date CVE data; pin if breakage occurs | Pin tag if Trivy updates break pipeline |
| L-013 | No rate limiting on Woodpecker webhook receiver | **RESOLVED:** Not a concern for single-node dev; reverse proxy with rate limiting needed for prod | Add reverse proxy before production deployment |
| L-014 | ~~Jenkins-based `k8s/` manifests are stale~~ | **RESOLVED:** Legacy `k8s/` manifests removed with the Jenkins stack | `compose.yaml` + `.woodpecker.yml` define the current stack |

### Security

| # | Limitation | Impact | Mitigation |
| - | ---------- | ------ | ---------- |
| L-015 | Woodpecker agent mounts `/var/run/docker.sock` | **RESOLVED:** Required for CNB builds; acceptable in dev; restrict in production via agent isolation or K8s pod security policies | Document production restrictions before scaling |
| L-016 | No Vault / Infisical integration | **RESOLVED:** Secrets managed via Woodpecker's SQLite store and `.env` file; Infisical runs in security plane but not wired to pipeline | Acceptable for single-node dev; wire Infisical to pipeline in future |

### CI/CD & Release

| # | Limitation | Impact | Mitigation |
| - | ---------- | ------ | ---------- |
| L-017 | ~~Release Please workflow fails when `RELEASE_PLEASE_TOKEN` secret is not configured and repository default workflow permissions are `read`~~ | **RESOLVED:** `scripts/release.sh` provides automated release process (tag, CHANGELOG, GitHub Release) independent of Release Please | Use `./scripts/release.sh vX.Y.Z` for automated releases; see `RELEASE_PROCESS.md` |

---

## Deprecations

| Item | Deprecated In | Replaced By | Removal Target |
| ---- | ------------- | ----------- | -------------- |
| ~~`docker-compose.yml`~~ | v0.2 (Woodpecker migration) | `compose.yaml` | **REMOVED** |
| ~~Jenkins `shared/` library (vars/)~~ | v0.2 | `.fawkespipe.yml` contract | **REMOVED** |
