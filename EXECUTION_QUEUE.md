# EXECUTION_QUEUE.md — uFawkesPipe

> **Horizon:** Weeks | **Owner:** Platform Engineering | **Review Cadence:** Weekly (Monday planning)

---

## Priority Tiers

### P0 — Blocks Release (Must complete before any v0.x tag)

| # | Task | Source | Acceptance Criteria | Skill(s) |
|---|------|--------|---------------------|----------|
| P0-1 | Complete `docs/KNOWN_LIMITATIONS.md` resolution — all items RESOLVED or mitigated | M1.5 | Zero "Unresolved" rows; each has Mitigation column filled | doc-reality-check, verification |
| P0-2 | `make test-acceptance` passes on fresh `make up` (no pre-warmed services) | M1.6 | Cold start: `make down -v && make up && make test-acceptance` → 0 failures | test-execution, e2e-happy-path |
| P0-3 | Update CHANGELOG.md for v0.3 with all M1.x deliverables | M1.6 | CHANGELOG follows Keep a Changelog format; entries link issues | release |

### P1 — This Sprint (Week of 2026-09-14)

| # | Task | Source | Acceptance Criteria | Skill(s) |
|---|------|--------|---------------------|----------|
| P1-1 | Fix `vuln-scan-fs` Trivy severity threshold alignment (HIGH/CRITICAL vs CRITICAL only) | KNOWN_LIMITATIONS L-008 follow-up | Trivy fs scan fails on HIGH+; config in `.fawkespipe.yml.example` matches | pipeline-policy, verification |
| P1-2 | Add `policy-check` step timeout (currently unbounded) | AGENTS.md §4 | Step has `timeout: 5` minutes; fails fast on OPA hang | pipeline-policy, governance-enforcement |
| P1-3 | Document suite-mode network topology in `docs/ARCHITECTURE.md` §12.2 (add diagram for security plane services) | ARCHITECTURE.md gap | Mermaid diagram shows defectdojo/infisical/trivy/falco on `fawkes-net` internal | documentation, design-compliance |
| P1-4 | Add `make test-policy` target running Conftest against local compose files | design.md §4 | `make test-policy` runs `conftest test --policy policy/ compose.yaml compose.suite.yaml .woodpecker.yml` | test-execution, pipeline-test-stage-validation |

### P2 — Next Sprint (Week of 2026-09-21)

| # | Task | Source | Acceptance Criteria | Skill(s) |
|---|------|--------|---------------------|----------|
| P2-1 | Wire DefectDojo API ingestion in `upload-defectdojo` step (replace stub curl) | M2.5 | Trivy JSON POSTed to `http://defectdojo:8080/api/v2/import-scan/`; returns 201 | pipe-to-obs-integration, build |
| P2-2 | Add SonarQube quality gate wait in generated pipeline (currently fire-and-forget) | `.fawkespipe.yml.example` gap | `sonarqube: qualityGate: true` produces polling step in generated `.woodpecker.yml` | pipeline-generation, build |
| P2-3 | Create `examples/fawkespipe-contract-migration/v0.3/` with worked example | M1.6 | Example shows v0.2 → v0.3 field changes; migration guide in `docs/` | documentation, template-scaffolding |
| P2-4 | Add GitHub Actions workflow for `make validate` on PR (mirror Woodpecker validate stage) | CI-local parity | `.github/workflows/validate.yml` runs yamllint, shellcheck, pytest unit | ci-local-parity, pipeline-generation |

### P3 — Backlog (Post v0.3 / H2)

| # | Task | Source | Acceptance Criteria | Skill(s) |
|---|------|--------|---------------------|----------|
| P3-1 | Woodpecker PostgreSQL migration (standalone → shared via uFawkesRes) | M2.1 | `compose.yaml` Woodpecker service uses external Postgres; SQLite volume optional | refactoring, k8s-design-validation |
| P3-2 | SonarQube PostgreSQL migration (embedded H2 → shared via uFawkesRes) | M2.1 | `compose.yaml` SonarQube uses external Postgres; H2 removed | refactoring, k8s-design-validation |
| P3-3 | OTEL metrics export from Woodpecker server → Prometheus scrape config | M2.2 | `WOODPECKER_PROMETHEUS_AUTH_TOKEN` works; Grafana dashboard shows pipeline duration | ufawkesobs-observability, build |
| P3-4 | Pipeline step traces via OTEL (Woodpecker native or wrapper) | M2.3 | Tempo shows per-pipeline spans; not just server request traces | ufawkesobs-observability, pipe-to-obs-integration |
| P3-5 | Alloy config for structured pipeline log parsing (JSON → Loki labels) | M2.4 | Loki queries show `stage`, `status`, `duration_ms` labels from step logs | ufawkesobs-observability, build |
| P3-6 | Automated release script (`scripts/release.sh`) implementing `RELEASE_PROCESS.md` | M3.3 | `./scripts/release.sh vX.Y.Z` cuts tag, CHANGELOG, GitHub Release, deploys | release, build |
| P3-7 | Kubernetes promotion path: Woodpecker K8s manifests + Helm chart | M3.4 | `docs/kubernetes-promotion.md` has working manifests; `make up-k8s` smoke test | manifest-generation, k8s-design-validation |

---

## Scope-Drift Protection

> **Before adding anything to this queue, check against VISION.md Non-Goals:**

| Non-Goal | Drift Symptom | Action |
|----------|---------------|--------|
| Multi-node / HA Woodpecker | Adding PostgreSQL to standalone `compose.yaml` | → Move to P3 backlog; suite mode handles this |
| K8s-native deployment | Writing K8s manifests in `k8s/` | → Document in `docs/kubernetes-promotion.md` only |
| External artifact repo | Adding Nexus/Harbor service | → Reject; OCI registry is the contract |
| Full DefectDojo integration | Building DefectDojo UI dashboards | → Scope to API ingestion only (P2-1) |
| GitOps controller integration | Adding Flux/Argo to compose | → Reject; app team concern |
| SSO/RBAC for platform | Adding Authelia to standalone | → Suite mode only (uFawkesRes) |
| Performance testing | Adding k6/Locust to CI | → Post-alpha (H3) |
| Custom pipeline DSL | Adding `script:` or `cel:` fields to contract | → Reject; declarative YAML only |

**If a task violates a non-goal → it does not enter the queue.** Escalate to VISION.md review (quarterly) if the non-goal itself needs changing.

---

## Bottom-Up Feedback Loop

> Learnings from `plan-for-the-day.md` retrospectives route back here:

| Date | Retrospective Insight | Queue Impact |
|------|----------------------|--------------|
| 2026-09-14 | (This session) — Pipeline contract generator needs integration tests for edge cases (empty stages, custom builders) | Added P1-5 (new): `scripts/generate_woodpecker_yml.py` contract test matrix |
| — | — | — |

**Process:** At end of each `plan-for-the-day.md` session, the retrospective section captures:
1. What took longer than expected?
2. What broke that wasn't in the queue?
3. What non-goal pressure appeared?
4. → Convert insights into P1/P2 tasks or VISION.md non-goal challenges.