# MILESTONES.md — uFawkesPipe

> **Horizon:** Months | **Owner:** Platform Engineering | **Review Cadence:** Monthly (sprint boundary)

---

## Horizon Map

| Horizon | Timeframe | Theme | Success Signal |
|---------|-----------|-------|----------------|
| **H1** | Months 1–3 (Now → Oct 2026) | **Contract hardening & acceptance automation** | `make test-acceptance` passes on fresh `make up`; new repo onboards in ≤30 min via contract |
| **H2** | Months 4–6 (Nov 2026 → Jan 2027) | **Suite-mode maturity & observability closure** | Suite mode (`make up-suite`) runs green end-to-end; DORA events flow to uFawkesObs dashboards |
| **H3** | Months 7–12 (Feb 2027 → Jul 2027) | **Production hardening & team onboarding** | 3+ app teams using contract in anger; <5% rework rate; release process documented & automated |

---

## Milestones

### H1 — Contract Hardening & Acceptance Automation (Current)

| Milestone | Deliverable | Status | Issue / PR | Target |
|-----------|-------------|--------|------------|--------|
| M1.1 | Acceptance test suite complete (stack health, auth, pipeline sim, scan artifacts, deploy webhook) | ✅ Done | #49, #52, #55 | Jul 2026 |
| M1.2 | Pipeline contract generator (`scripts/generate_woodpecker_yml.py`) covers all `stages.*` fields | ✅ Done | #47 | Jul 2026 |
| M1.3 | `notify-obs` emits structured DORA deployment event to OTEL collector (suite mode) | ✅ Done | #58 | Aug 2026 |
| M1.4 | Security plane merged (DefectDojo, Infisical, Trivy server, Falco + policy-check) | ✅ Done | #62 | Aug 2026 |
| M1.5 | All `docs/KNOWN_LIMITATIONS.md` items marked RESOLVED or have mitigation | 🔄 In progress | #65 | Sep 2026 |
| M1.6 | **v0.3 Release** — Tag, CHANGELOG, GitHub Release, acceptance suite green | ⏳ Planned | — | **Sep 2026** |

### H2 — Suite-Mode Maturity & Observability Closure

| Milestone | Deliverable | Status | Issue / PR | Target |
|-----------|-------------|--------|------------|--------|
| M2.1 | Suite mode `make up-suite` passes full acceptance suite against uFawkesRes + uFawkesObs | ⏳ Planned | — | Oct 2026 |
| M2.2 | Woodpecker metrics scraped by Prometheus (uFawkesObs) — dashboards show pipeline duration, success rate | ⏳ Planned | — | Nov 2026 |
| M2.3 | OTEL traces from Woodpecker server visible in Tempo/Grafana | ⏳ Planned | — | Nov 2026 |
| M2.4 | Alloy log scraping → Loki working for all services (including pipeline step logs) | ⏳ Planned | — | Dec 2026 |
| M2.5 | DefectDojo findings ingestion wired (Trivy JSON → DefectDojo API) | ⏳ Planned | — | Dec 2026 |
| M2.6 | **v1.0 Release** — First "team-ready" tag with suite mode documented | ⏳ Planned | — | **Jan 2027** |

### H3 — Production Hardening & Team Onboarding

| Milestone | Deliverable | Status | Issue / PR | Target |
|-----------|-------------|--------|------------|--------|
| M3.1 | 3+ app teams onboarded via `.fawkespipe.yml` contract (tracked in `examples/`) | ⏳ Planned | — | Mar 2027 |
| M3.2 | Rework rate < 10% (PRs needing repair-flow after merge attempt) | ⏳ Planned | — | Apr 2027 |
| M3.3 | Release process automated (`RELEASE_PROCESS.md` executed by script) | ⏳ Planned | — | May 2027 |
| M3.4 | Kubernetes promotion path tested end-to-end (compose → K8s) | ⏳ Planned | — | Jun 2027 |
| M3.5 | **v2.0 Release** — Production-hardened, multi-team validated | ⏳ Planned | — | **Jul 2027** |

---

## Release Gates

A release (tag + GitHub Release + CHANGELOG) ships **only when all gates pass**:

| Gate | Check | How Verified |
|------|-------|--------------|
| **Tests** | `make test-unit && make test-integration && make test-acceptance` all pass | Local + CI |
| **Docs Updated** | CHANGELOG.md, README.md, ARCHITECTURE.md (if changed), KNOWN_LIMITATIONS.md | `git diff docs/` |
| **Contract Stable** | `.fawkespipe.yml.example` version bumped; migration example in `examples/` if breaking | `examples/fawkespipe-contract-migration/` |
| **Tag Created** | Semver tag pushed (`git tag vX.Y.Z && git push --tags`) | GitHub Releases page |
| **Deploy + Verify** | `make up` (standalone) and `make up-suite` (suite, if uFawkesRes/Obs available) both green | Manual or CI |

> **Pre-alpha exception:** H1 releases (v0.x) may ship with suite-mode gate as "verify when uFawkesRes/Obs available" — document in release notes.

---

## Traceability: Milestones → Vision Principles

| Milestone | Principle 1: Contract-first | Principle 2: Polyglot/CNB | Principle 3: Hard security | Principle 4: Single-node → suite | Principle 5: DORA native | Principle 6: No secrets | Principle 7: Acceptance-tested | Principle 8: Woodpecker-native |
|-----------|----------------------------|---------------------------|----------------------------|----------------------------------|--------------------------|-------------------------|-------------------------------|-------------------------------|
| M1.1 | ✅ | | ✅ | ✅ | | | ✅ | ✅ |
| M1.2 | ✅ | ✅ | | | | | | ✅ |
| M1.3 | | | | | ✅ | | | ✅ |
| M1.4 | | | ✅ | ✅ | | ✅ | | ✅ |
| M1.5 | | | | ✅ | | | ✅ | |
| M2.1 | | | | ✅ | | | ✅ | |
| M2.2 | | | | | ✅ | | | |
| M2.3 | | | | | ✅ | | | |
| M2.4 | | | | | ✅ | | | |
| M2.5 | | | ✅ | | | | ✅ | |
| M3.1 | ✅ | ✅ | | | | | | |
| M3.2 | | | | | | | ✅ | |
| M3.3 | | | | | | | | |
| M3.4 | | | | ✅ | | | | |

> **Reading the table:** ✅ = milestone directly advances this principle. Blank = indirect or no impact.