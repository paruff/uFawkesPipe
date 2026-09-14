# VISION.md — uFawkesPipe

> **Horizon:** Years | **Owner:** Platform Engineering (solo contributor) | **Review Cadence:** Quarterly (or when north star shifts)
> **Stage:** Pre-alpha | **Persona:** DevOps engineer / platform engineer supporting an internal developer platform

---

## North Star

**A CI/CD platform in Docker Compose that small teams can trust to run their pipelines reliably — before the full IDP launches.**

---

## Core Principles (4–8, specific to this product)

| # | Principle | What It Means in Practice |
|---|-----------|---------------------------|
| 1 | **Contract-first, not config-first** | App teams declare *what* in `.fawkespipe.yml`; the platform handles *how*. No per-app pipeline YAML. |
| 2 | **Polyglot by default via CNB** | Cloud Native Buildpacks handles Java, Python, Node.js, Go, Ruby out of the box. Dockerfile is an escape hatch, not the default. |
| 3 | **Security gates are hard, not advisory** | Gitleaks, Trivy, SonarQube quality gates — non-zero exit = pipeline stops. No "warn-only" security steps. |
| 4 | **Single-node dev, production-ready patterns** | `make up` spins the full stack on a laptop. Same compose files promote to suite mode with shared infra — no rewrite. |
| 5 | **DORA signals are native, not bolted on** | Every pipeline step emits structured JSON logs; `notify-obs` posts deployment events to OTEL. Lead time and deployment frequency are measurable from day one. |
| 6 | **No secrets in repo, ever** | `.env` is gitignored. Woodpecker secret store + pre-commit Gitleaks are the only paths. |
| 7 | **Acceptance-tested, not hope-tested** | `make test-acceptance` verifies stack health, auth, pipeline structure, scan artifacts, deploy webhook — automatically. Green = trustworthy. |
| 8 | **Woodpecker-native, not Jenkins-ported** | Single `.woodpecker.yml` replaces JCasC + plugin matrix. Docker-in-Docker is native, not a plugin hack. |

---

## Non-Goals (Explicit for Pre-Alpha Stage)

| # | Non-Goal | Rationale |
|---|----------|-----------|
| 1 | **Multi-node / HA Woodpecker** | SQLite is fine for single-node dev. PostgreSQL migration is a suite-mode concern (uFawkesRes), not a v0.x concern. |
| 2 | **Kubernetes-native deployment** | K8s promotion path is documented (`docs/kubernetes-promotion.md`) but not built. Compose is the delivery vehicle. |
| 3 | **External artifact repository (Nexus, Harbor, etc.)** | OCI registry (DockerHub/GHCR) is the artifact store. Nexus was removed in the Jenkins→Woodpecker migration. |
| 4 | **Full DefectDojo integration** | DefectDojo runs in the security plane but findings ingestion is stubbed. v0.x scope stops at Trivy → filesystem JSON. |
| 5 | **GitOps controller (Flux/Argo) integration** | uFawkesPipe *is* the CI/CD engine. GitOps for *applications* is the app team's concern, not the platform's. |
| 6 | **SSO / RBAC for the platform itself** | `WOODPECKER_OPEN=true` for dev. Authelia SSO comes via uFawkesRes in suite mode. Not a pre-alpha concern. |
| 7 | **Performance / stress testing** | Functional correctness first. Load testing is post-alpha when real teams onboard. |
| 8 | **Custom pipeline DSL / scripting** | `.fawkespipe.yml` is declarative YAML. No Groovy, no CEL, no custom scripts in the contract. |

---

## Single Riskiest Assumption

> **"App teams will adopt `.fawkespipe.yml` instead of writing their own `.woodpecker.yml`."**

**Why this is the riskiest:** The entire value proposition — contract-first, polyglot, zero per-app pipeline YAML — collapses if teams bypass the contract and write raw Woodpecker pipelines. The contract must be *easier* than the alternative, not just "standardized."

**Validation signal:** Time-to-first-green-pipeline for a new repo onboarding via contract vs. raw Woodpecker. Target: contract path ≤ 30 min, raw path > 2 hours (current reality).

---

## How This Connects

| Document | What It Answers |
|----------|-----------------|
| **MILESTONES.md** | What we ship and when — monthly/quarterly horizons mapped to principles |
| **EXECUTION_QUEUE.md** | What we work on this week/next — priority tiers, scope-drift guard |
| **plan-for-the-day.md** | What we do *today* — single goal, TDD protocol, retrospective |
| **docs/product/discovery-draft.md** | The JTBD, riskiest assumption, and measurable acceptance criterion behind the current increment |
| **docs/product/spec.md** | Numbered functional requirements tracing to discovery-draft |
| **docs/ARCHITECTURE.md** | How components connect — service map, data flows, network topology, suite mode |
| **docs/KNOWN_LIMITATIONS.md** | What's broken or missing — living document, agents must not make these worse |
| **docs/CHANGE_IMPACT_MAP.md** | What breaks when — cross-plane impact of contract, compose, pipeline changes |
| **docs/AI_STANCE.md** | AI tooling policy for this repo — model selection, cost tracking, stance on AI-generated code |
| **docs/RELEASE_PROCESS.md** | How we cut a release — gates, changelog, tagging, verification |
| **docs/DEPLOYMENT_STRATEGY.md** | How the platform itself deploys — standalone vs suite, rollback, progressive delivery N/A |

> **Note on missing cross-cutting docs:** `CONTRACTS.md` does not apply — uFawkesPipe has no external integration surface beyond the `.fawkespipe.yml` contract (which *is* the contract). `AI_STANCE.md`, `RELEASE_PROCESS.md`, `DEPLOYMENT_STRATEGY.md` do not yet exist; they will be created when the corresponding process matures (see MILESTONES.md H2).