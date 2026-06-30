# AGENTS.md — uFawkesPipe

> Universal instructions for all agents: GitHub Copilot, VS Code agent mode, Claude.
> uFawkesPipe is the **Integration & Delivery Plane of the Fawkes IDP family**.
> It provides a Jenkins-based CI/CD platform via Docker Compose with a standardised
> pipeline contract for polyglot applications.
>
> Shared template across all repos this harness operates on. Keep section numbers
> 4, 6, 7 as-is — `review.md`, `test.md`, and `feature-flow.md` reference them
> by number. Everything else may be trimmed to what this repo actually needs.
>
> What's deliberately NOT here: model selection, token budgets, premium request
> accounting — see `docs/MODEL_POLICY.md` if one exists for this repo.

---

## 1. Identity

- **Repo:** `paruff/uFawkesPipe`
- **What this is:** Integration & Delivery Plane of the Fawkes IDP family. Provides a Jenkins-based CI/CD platform via Docker Compose with a standardised pipeline contract for polyglot applications.
- **Suite membership:** uFawkesAI

**Stack:**

| Component | Role |
| --- | --- |
| Jenkins (via Docker Compose) | Pipeline orchestration |
| Docker Compose | Service orchestration for the platform itself |
| `jenkins/` | Jenkins configuration as code (JCasC), plugin lists |
| `k8s/` | Kubernetes deployment manifests for running uFawkesPipe on K8s |
| `pack/` | Buildpack configuration for app builds |
| `shared/` | Shared pipeline libraries and utilities |
| `Jenkinsfile` | Pipeline definition for uFawkesPipe's own CI |
| `Makefile` | Developer convenience targets |
| `.fawkespipe.yml` | Pipeline contract — app teams configure this |

---

## 2. Where the Agents Live

Agents and skills are shared, not repo-local: `~/.config/opencode/agents/`
and `~/.config/opencode/skills/`. This file does not redefine them — it
tells the shared agents how to behave *in this repo specifically*.

Standard pipeline, in order:

```
discover → spec → design → plan
                              │
                              ▼
                        feature-flow
        (branch → build → test-execution → review →
         verification → cross-validation → delivery-prep)
                              │
                              ▼
                    [push, PR, CI, human merge]
                              │
                  ┌───────────┴───────────┐
                  ▼                       ▼
            repair-flow              release → measure → learn
         (if CI disagrees          (post-merge cadence,
          with local test)          closes the loop)
```

`discovery-flow` routes into the top half (discovery through planning).
`feature-flow` owns everything from a planned feature to an open PR.
It never merges — that is always human-gated. `repair-flow` is the
CI-failure-specific repair loop, separate from feature-flow's own local
test gate. `measure` and `learn` run on schedule or trigger, not as
steps another agent calls directly.

---

## 3. Context Files — Read Before Generating Anything

| Priority | File | What You Learn |
| -------- | ---- | -------------- |
| 1 | `AGENTS.md` (this file) | Identity, governance, GitOps contract |
| 2 | `compose.yaml` + `compose.suite.yaml` | Service versions, configuration, standalone vs suite mode |
| 3 | `.fawkespipe.yml.example` | The pipeline contract that app teams use |
| 4 | `docs/ARCHITECTURE.md` | How components connect |
| 5 | `docs/KNOWN_LIMITATIONS.md` | Known issues — do not make these worse |
| 6 | `docs/CHANGE_IMPACT_MAP.md` | What breaks when pipeline contract changes |

**Gaps** (noted — agents proceed with what's available):
- `docs/GOLDEN_PATH.md` — exists. Read for the canonical idea → deploy workflow.
- `docs/MODEL_POLICY.md` — exists. Read for model selection and cost tracking.

---

## 4. Architecture Rules — Never Violate These

### docker-compose.yml

- All image versions pinned — no `latest` tags
- Secrets via `.env` (gitignored) — never inline
- Every service has `healthcheck:`
- Jenkins home volume is named and persistent

### Jenkins Configuration (`jenkins/`)

- **Configuration as Code (JCasC)** — all Jenkins config in YAML, never via UI clicks
- Plugin versions pinned in plugin list — no auto-update in production
- No credentials stored in JCasC YAML — use Jenkins credential store via environment variables
- Seed jobs define all pipeline jobs — no manually created jobs

### Shared Library (`shared/`)

- Pipeline steps are functions in `vars/` — one file per step
- Steps must be idempotent — safe to re-run
- No hardcoded registry URLs, cluster names, or environment names
- All steps log: start time, what they're doing, finish time (DORA logging)

### Jenkinsfile

- DORA logging required: log start timestamp, commit SHA, finish timestamp per stage
- Stages: Checkout → Build → Test → Security Scan → Publish → Deploy (in that order)
- Failed stages must capture and archive artifacts before failing the build
- No inline credentials — use `withCredentials()` block

### Pipeline Contract (`.fawkespipe.yml`)

- This is the interface app teams configure — treat changes as breaking changes
- New fields must be optional with sensible defaults
- Removed fields require a deprecation period and migration guide

### Kubernetes Manifests (`k8s/`)

- No `latest` image tags
- Resource limits on all containers
- Labels: `plane: ufawkespipe`, `managed-by: fawkes`

### Coding Standards

**Groovy (Jenkinsfile, shared/):**
- Functions over repeated blocks
- `try/catch/finally` with artifact archival on failure
- DORA timestamp logging on every stage
- Conventional commits: `feat(pipeline):`, `fix(jenkins):`, `chore:`

**YAML (docker-compose, JCasC, k8s):**
- `yamllint` must pass
- 2-space indentation
- Quoted strings for values that could be misread

**Bash (validate.sh, scripts/):**
- `set -euo pipefail` at top
- `shellcheck` must pass

---

## 5. The PM–Agent Contract

### Agents MAY Do Without Asking

- Read any file
- Edit code, tests, docs within the scope of an assigned task
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
- Adding or removing dependencies
- Changing public interfaces or API contracts

### Agents Must NEVER

- Commit secrets, credentials, API keys, or `.env` files
- Use `latest` image tags anywhere
- Store credentials in JCasC YAML
- Create Jenkins jobs via UI (use seed jobs)
- Push to trunk directly or merge their own PRs
- Apply `large-pr-approved` (or equivalent override) label — humans only
- Delete tests to make a build pass
- Mark a task complete when validation failed

---

## 6. TDD Commit Order

```
1. test: add failing tests for [feature]   ← CI fails here intentionally
2. feat: implement [feature] to pass tests
3. refactor: clean up [feature] if needed
```

Never combine a failing test commit with an implementation commit.

---

## 7. AI-Assisted Review Block

Every PR opened by an agent must include this block in its description.
`review.md` checks for this literal structure — if you change the
headings, update `review.md`'s check to match.

```markdown
## AI-Assisted Review Block

**What does this PR do?**
[...]

**What could go wrong?**
[...]

**What tests cover this change?**
[...]

**Architecture check:**
[...]

**What I was NOT sure about:**
[...]
```

For uFawkesPipe specifically, every PR must also cover:
- **Pipeline stages affected** — which stages were added, removed, or modified
- **How tested** — local `make up` + pipeline run
- **Breaking change check** — did `.fawkespipe.yml` contract change? If so, migration guide written?
- **Credentials check** — nothing sensitive committed

---

## 8. GitOps / Trunk-Based Delivery Contract

- Development happens on feature branches off trunk (`main`); never commit directly to trunk.
- Branch naming: `feature/<short-slug>` — keep short and descriptive.
- CI runs on push and on PR. `feature-flow`'s local test-execution and CI are separate events — if CI fails after local tests passed, `repair-flow` handles it; that is not a feature-flow failure.
- PR size > 400 changed lines → CI blocks. Override requires an explicit human-applied label — agents never apply it themselves.
- Pipeline contract changes (`.fawkespipe.yml`) require a migration example in `examples/` before merging.
- Jenkins plugin updates require a full pipeline test run on a branch before merging.
- Merge to trunk requires: green CI, review APPROVED, verification PASS, cross-validation PASS, and human approval. All five, every time.
- Rework rate > 10% (PRs requiring `repair-flow` after merge attempt, or requiring more than one review/verification cycle): stop adding new scope, fix the instructions or gates that are letting bad output through before continuing.

---

## 9. Known Limitations

See `docs/KNOWN_LIMITATIONS.md` for the full list. Key items agents should be aware of:

- The `k8s/` manifests still reference the legacy Jenkins stack (not the current Woodpecker stack).
- `notify-obs` is a stub — no DORA deployment events are actually emitted yet.
- No automated integration or E2E tests exist — only unit tests.
- No Gitleaks secrets scan in CI (only pre-commit hook).

---

## 10. Suite Integration

uFawkesPipe is part of the **uFawkesAI** suite of IDP planes. It supports two modes:

- **Standalone** (`make up`) — runs independently with SQLite/H2 storage, no external dependencies
- **Suite** (`make up-suite`) — connects to uFawkesRes + uFawkesObs for shared PostgreSQL, OTEL telemetry, and Traefik ingress

| Plane | Relationship |
| ----- | ------------ |
| **uFawkesRes** | Suite mode: shared PostgreSQL (fawkes-postgres:5432), Valkey cache, Traefik ingress, Authelia SSO. Connect via `fawkes-backbone-net`. |
| **uFawkesObs** | Suite mode: OTEL Collector (otel-collector:4317 gRPC, :4318 HTTP) for traces, metrics, logs, and deployment events. Connect via `observability-lab`. Alloy scrapes Docker logs. |
| **developerd** | Developer tooling triggered by uFawkesPipe pipeline events. Changes to `.fawkespipe.yml` contract or pipeline stage names may affect developer tooling. |
| **fawkes** | Full IDP uses uFawkesPipe as its CI/CD engine. Jenkins webhook port changes affect GitHub webhook config. Check `docs/CHANGE_IMPACT_MAP.md` before modifying anything with cross-plane impact. |

---

## Appendix — Directory & File Map

| Path | Language | What Lives Here | Do Not |
| ---- | -------- | --------------- | ------ |
| `compose.yaml` | YAML | Woodpecker server + agent, SonarQube, Portainer | Hardcode credentials |
| `.woodpecker.yml` | YAML | CI pipeline definition for uFawkesPipe itself | Store secrets here |
| `.fawkespipe.yml` | YAML | Pipeline contract — configured by app teams (example in `.fawkespipe.yml.example`) | Modify without migration guide |
| `docker-compose.yml` | YAML | **Deprecated** — legacy Jenkins stack, retained for reference | Use for new deployments |
| `jenkins/` | YAML / Groovy | JCasC config, plugin lists, seed jobs (**legacy**) | Store secrets here |
| `k8s/` | YAML | K8s manifests (**Jenkins-based, needs update**) | Use `latest` image tags |
| `pack/` | TOML / YAML | Buildpack builder and extension configs | Hardcode language versions |
| `shared/` | Groovy / — | Shared Jenkins pipeline library (**legacy**) / shared workspace | Put app logic here |
| `examples/` | YAML | Example `.fawkespipe.yml` for different stacks | Use as production config |
| `docs/` | Markdown | Architecture, pipeline contract, runbooks | — |
| `tests/` | Python | pytest unit tests (contract validation) | Skip before committing |
| `scripts/` | Bash | Git hooks (pre-commit, commit-msg, validate-agents) | — |
| `Makefile` | Make | `make up`, `make validate`, `make test-*` targets | Put logic that belongs in scripts |
| `validate.sh` | Bash | Pre-flight validation script | Bypass with `--no-verify` |
