# Known Limitations — uFawkesPipe

> Agents should read this before building to avoid making these worse.
> This is a living document — add entries as you discover them.

---

## Current Limitations

### Architecture & Documentation

| # | Limitation | Impact | Mitigation |
| - | ---------- | ------ | ---------- |
| L-001 | `docs/ARCHITECTURE.md` documents the Woodpecker-based stack, but `k8s/` manifests and `docker-compose.yml` still reference the legacy Jenkins architecture | Agents may infer inconsistent architecture depending on which files they read | Agents should treat `compose.yaml` and `.woodpecker.yml` as the source of truth for the current stack; treat `docker-compose.yml` as legacy reference only |
| L-002 | No `docs/GOLDEN_PATH.md` exists | Agents lack a documented "idea → deploy" workflow to stay on the golden path | Agents should infer workflow from AGENTS.md §8 (GitOps contract) and ARCHITECTURE.md |
| L-003 | No `docs/MODEL_POLICY.md` exists | Agent model selection and cost tracking is ad-hoc | Currently using model routing from shared agent configuration |
| L-004 | `.github/copilot-instructions.md` and `.github/instructions/` don't exist | No path-scoped instruction files for Copilot | Agents proceed with AGENTS.md as the primary instruction source |

### Pipeline & CI

| # | Limitation | Impact | Mitigation |
| - | ---------- | ------ | ---------- |
| L-005 | The pipeline contract (`.fawkespipe.yml.example`) is aspirational — `.woodpecker.yml` doesn't actually read it at runtime | The clean separation between platform and app config isn't fully realized | Platform CI uses `.woodpecker.yml` directly; `.fawkespipe.yml` is contract-documented but not executed by the runner |
| L-006 | `notify-obs` step is a stub — it echoes a message instead of POSTing to uFawkesObs | No DORA deployment events are actually emitted | The payload schema is documented in `specification.md`; implement when uFawkesObs endpoint is available |
| L-007 | No automated integration or E2E tests exist — only unit tests | Pipeline contract changes are only caught at the schema level, not at runtime | `make test-integration` and `make test-smoke` are defined but not implemented |
| L-008 | `security-scan` runs only on `push → main`, not on PRs | Vulnerabilities are detected late (after merge, not before) | Safe for solo-contributor velocity; revisit when team grows |
| L-009 | No Gitleaks secrets scan in the Woodpecker pipeline | Secrets committed in PRs won't be caught in CI | Pre-commit Gitleaks hook is the only gate; v0.2 spec called for a CI secrets-scan step |

### Stack & Infrastructure

| # | Limitation | Impact | Mitigation |
| - | ---------- | ------ | ---------- |
| L-010 | Woodpecker uses SQLite (single-file database) | Not suitable for multi-server HA; data loss risk if volume is corrupted | Acceptable for single-node dev. Migrate to PostgreSQL when scaling. |
| L-011 | SonarQube uses embedded H2 database (no PostgreSQL container in `compose.yaml`) | Data loss on container restart; limited scaling | Acceptable for dev. Add PostgreSQL when promoting to prod. |
| L-012 | Trivy image uses `latest` tag (intentional, documented exception) | Potential breaking changes on Trivy upgrades; no reproducibility | Accepted trade-off for up-to-date CVE data. Pin if breakage occurs. |
| L-013 | No rate limiting on Woodpecker webhook receiver | Malicious or misconfigured webhooks could overload the server | Not a concern for single-node dev. Add reverse proxy with rate limiting for prod. |
| L-014 | Jenkins-based `k8s/` manifests are stale | Can't use `kubectl apply -f k8s/` to deploy the current Woodpecker stack | Either update manifests or remove them. Documented in ARCHITECTURE.md §9. |

### Security

| # | Limitation | Impact | Mitigation |
| - | ---------- | ------ | ---------- |
| L-015 | Woodpecker agent mounts `/var/run/docker.sock` | Full host Docker access from pipeline step containers (Docker-in-Docker) | Required for CNB builds. Acceptable in dev; restrict in production via agent isolation or K8s pod security policies. |
| L-016 | No Vault / Infisical integration | Secrets managed via Woodpecker's SQLite store and `.env` file | Acceptable for single-node dev. Production hardening is future scope. |

---

## Deprecations

| Item | Deprecated In | Replaced By | Removal Target |
| ---- | ------------- | ----------- | -------------- |
| `docker-compose.yml` | v0.2 (Woodpecker migration) | `compose.yaml` | When no references remain |
| Jenkins `shared/` library (vars/) | v0.2 | `.fawkespipe.yml` contract | After full contract implementation |
