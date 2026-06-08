# Agent Instructions — uFawkesPipe

> Universal instructions for all agents: GitHub Copilot, VS Code agent mode, Claude.
> uFawkesPipe is the **Integration & Delivery Plane of the Fawkes IDP family**.
> It provides a Jenkins-based CI/CD platform via Docker Compose with a standardised
> pipeline contract for polyglot applications.
> **Do not modify this file without maintainer approval.**

---

## 1. What uFawkesPipe Is

uFawkesPipe is a production-ready CI/CD platform built on Jenkins, designed for polyglot
application development with a standardised pipeline contract. It provides automated
build, test, security scanning, and deployment capabilities via Docker Compose.

**Stack:**
| Component | Role |
|---|---|
| Jenkins (via Docker Compose) | Pipeline orchestration |
| Docker Compose | Service orchestration for the platform itself |
| `jenkins/` | Jenkins configuration as code (JCasC), plugin lists |
| `k8s/` | Kubernetes deployment manifests for running uFawkesPipe on K8s |
| `pack/` | Buildpack configuration for app builds |
| `shared/` | Shared pipeline libraries and utilities |
| `Jenkinsfile` | Pipeline definition for uFawkesPipe's own CI |
| `Makefile` | Developer convenience targets |
| `.fawkespipe.yml` | Pipeline contract — app teams configure this |

**Repository:** github.com/paruff/uFawkesPipe

---

## 2. Directory & File Map

| Path | Language | What Lives Here | Do Not |
|---|---|---|---|
| `docker-compose.yml` | YAML | Jenkins + supporting services | Hardcode credentials |
| `jenkins/` | YAML / Groovy | JCasC config, plugin lists, seed jobs | Store secrets here |
| `k8s/` | YAML | K8s manifests for uFawkesPipe on Kubernetes | Use `latest` image tags |
| `pack/` | TOML / YAML | Buildpack builder and extension configs | Hardcode language versions |
| `shared/` | Groovy | Shared Jenkins pipeline library steps | Put app logic here |
| `examples/` | Various | Example `.fawkespipe.yml` for different stacks | Use as production config |
| `docs/` | Markdown | Architecture, pipeline contract reference, runbooks | |
| `Jenkinsfile` | Groovy | uFawkesPipe's own CI pipeline | Hardcode credentials |
| `Makefile` | Make | `make up`, `make down`, `make validate` targets | Put logic that belongs in scripts |
| `validate.sh` | Bash | Pre-flight validation script | Bypass with `--no-verify` |

---

## 3. Context Files — Read Before Generating Anything

| Priority | File | What You Learn |
|---|---|---|
| 1 | `AGENTS.md` (this file) | Stack, boundaries, PM contract |
| 2 | `docker-compose.yml` | Current service versions and configuration |
| 3 | `.fawkespipe.yml.example` | The pipeline contract that app teams use |
| 4 | `docs/ARCHITECTURE.md` | How Jenkins, Docker, and Buildpacks fit together |
| 5 | `docs/KNOWN_LIMITATIONS.md` | Known issues — do not make these worse |
| 6 | `docs/CHANGE_IMPACT_MAP.md` | What breaks when pipeline contract changes |

---

## 4. Architecture Rules — Never Violate These

### docker-compose.yml
- All image versions pinned — no `latest` tags
- Secrets via `.env` (gitignored) — never inline
- Every service has `healthcheck:`
- Jenkins home volume is named and persistent

### Jenkins Configuration (jenkins/)
- **Configuration as Code (JCasC)** — all Jenkins config in YAML, never via UI clicks
- Plugin versions pinned in plugin list — no auto-update in production
- No credentials stored in JCasC YAML — use Jenkins credential store via environment variables
- Seed jobs define all pipeline jobs — no manually created jobs

### Shared Library (shared/)
- Pipeline steps are functions in `vars/` — one file per step
- Steps must be idempotent — safe to re-run
- No hardcoded registry URLs, cluster names, or environment names
- All steps log: start time, what they're doing, finish time (DORA logging)

### Jenkinsfile
- DORA logging required: log start timestamp, commit SHA, finish timestamp per stage
- Stages: Checkout → Build → Test → Security Scan → Publish → Deploy (in that order)
- Failed stages must capture and archive artifacts before failing the build
- No inline credentials — use `withCredentials()` block

### .fawkespipe.yml (pipeline contract)
- This is the interface app teams configure — treat changes as breaking changes
- New fields must be optional with sensible defaults
- Removed fields require a deprecation period and migration guide

### k8s/
- No `latest` image tags
- Resource limits on all containers
- Labels: `plane: ufawkespipe`, `managed-by: fawkes`

---

## 5. The PM–Agent Contract

### Agents MAY Do Without Asking
- Read any file
- Edit `docs/`, `examples/`, `Makefile` convenience targets
- Add or update shared library steps in `shared/vars/`
- Run: `make validate`, `yamllint`, `shellcheck`
- Open draft PRs

### Agents MUST Ask Before
- Changing Jenkins image version or plugin versions
- Modifying `.fawkespipe.yml` pipeline contract fields
- Changing `docker-compose.yml` service structure
- Adding new stages to the standard pipeline
- Modifying `k8s/` manifests

### Agents Must NEVER
- Commit `.env`, credentials, tokens, or API keys
- Use `latest` image tags anywhere
- Store credentials in JCasC YAML
- Create Jenkins jobs via UI (use seed jobs)
- Push to `main` directly or merge their own PRs
- Apply `large-pr-approved` label (humans only)

---

## 6. Coding Standards

### Groovy (Jenkinsfile, shared/)
- Functions over repeated blocks
- `try/catch/finally` with artifact archival on failure
- DORA timestamp logging on every stage
- Conventional commits: `feat(pipeline):`, `fix(jenkins):`, `chore:`

### YAML (docker-compose, JCasC, k8s)
- `yamllint` must pass
- 2-space indentation
- Quoted strings for values that could be misread

### Bash (validate.sh, scripts/)
- `set -euo pipefail` at top
- `shellcheck` must pass

---

## 7. PR Requirements

Every PR must include the AI-Assisted Review Block:
- What pipeline stages are affected
- How tested (local `make up` + pipeline run)
- Breaking change check on `.fawkespipe.yml` contract
- Credentials check: nothing sensitive committed

---

## 8. Instability Safeguards

- PR size > 400 lines → CI blocks. `large-pr-approved` to override (humans only).
- Pipeline contract changes require a migration example in `examples/`
- Jenkins plugin updates require a test run on a branch before merging
- Rework rate > 10%: stop adding pipeline stages, fix instructions

---

## 9. Integration with Other Planes

- **Obstackd**: uFawkesPipe sends pipeline traces to Obstackd's OTEL Collector (port 4317)
- **developerd**: Developer tooling triggered by uFawkesPipe pipeline events
- **fawkes**: Full IDP uses uFawkesPipe as its CI/CD engine; check fawkes CHANGE_IMPACT_MAP

---

## 10. See Also

- `.github/copilot-instructions.md` — Copilot-specific subset
- `.github/instructions/` — path-scoped instruction files
- `docs/PROMPT_LIBRARY.md` — tested prompt templates
- `docs/CHANGE_IMPACT_MAP.md` — cross-component impact
