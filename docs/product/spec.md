# Specification — uFawkesPipe Planning Cascade

> **Version:** 1.0.0 | **Date:** 2026-09-14 | **Status:** Draft
> **References:** `docs/product/discovery-draft.md` (DD-1 through DD-6)

---

## Functional Requirements

### FR-1: VISION.md — North Star & Principles (DD-1, DD-2)

| ID | Requirement | Trace |
|----|-------------|-------|
| FR-1.1 | VISION.md states the north star: "A CI/CD platform in Docker Compose that small teams can trust to run their pipelines reliably — before the full IDP launches." | DD-1 |
| FR-1.2 | VISION.md lists 4–8 core principles specific to uFawkesPipe (contract-first, polyglot/CNB, hard security gates, single-node→suite, DORA-native, no secrets, acceptance-tested, Woodpecker-native). | DD-1 |
| FR-1.3 | VISION.md has an explicit Non-Goals table for pre-alpha stage with ≥8 items, each with rationale. | DD-2 |
| FR-1.4 | VISION.md names the single riskiest assumption: "App teams will adopt `.fawkespipe.yml` instead of writing their own `.woodpecker.yml`." with validation signal. | DD-2 |
| FR-1.5 | VISION.md includes a "How This Connects" table linking to MILESTONES, EXECUTION_QUEUE, plan-for-the-day, discovery-draft, spec, ARCHITECTURE, KNOWN_LIMITATIONS, CHANGE_IMPACT_MAP, AI_STANCE, RELEASE_PROCESS, DEPLOYMENT_STRATEGY. | DD-1 |

### FR-2: MILESTONES.md — Horizon Map & Release Gates (DD-1, DD-3)

| ID | Requirement | Trace |
|----|-------------|-------|
| FR-2.1 | MILESTONES.md defines three horizons: H1 (Months 1–3), H2 (Months 4–6), H3 (Months 7–12) with theme and success signal each. | DD-1 |
| FR-2.2 | H1 milestones (M1.1–M1.6) cover acceptance suite, contract generator, notify-obs, security plane merge, KNOWN_LIMITATIONS resolution, v0.3 release. | DD-3 |
| FR-2.3 | H2 milestones (M2.1–M2.6) cover suite-mode maturity, observability closure, DefectDojo ingestion, v1.0 release. | DD-3 |
| FR-2.4 | H3 milestones (M3.1–M3.5) cover team onboarding, rework rate <10%, release automation, K8s promotion, v2.0 release. | DD-3 |
| FR-2.5 | MILESTONES.md defines Release Gates table: Tests, Docs Updated, Contract Stable, Tag Created, Deploy+Verify — with verification method each. | DD-3 |
| FR-2.6 | MILESTONES.md includes Traceability matrix mapping each milestone to the 8 Vision Principles. | DD-1 |

### FR-3: EXECUTION_QUEUE.md — Priority Tiers & Drift Protection (DD-1, DD-4)

| ID | Requirement | Trace |
|----|-------------|-------|
| FR-3.1 | EXECUTION_QUEUE.md defines P0 (blocks release), P1 (this sprint), P2 (next sprint), P3 (backlog) with task tables. | DD-1 |
| FR-3.2 | Each task has: Queue Ref, Task description, Source (milestone/issue), Acceptance Criteria, Skill(s). | DD-4 |
| FR-3.3 | P0 tasks: KNOWN_LIMITATIONS resolution, cold-start acceptance test pass, CHANGELOG for v0.3. | M1.5, M1.6 |
| FR-3.4 | P1 tasks: Trivy severity alignment, policy-check timeout, suite-mode architecture docs, make test-policy target. | Current sprint |
| FR-3.5 | EXECUTION_QUEUE.md includes Scope-Drift Protection table checking each Non-Goal from VISION.md against drift symptoms. | DD-2 |
| FR-3.6 | EXECUTION_QUEUE.md includes Bottom-Up Feedback Loop table for retrospective insights → queue deltas. | DD-1 |

### FR-4: plan-for-the-day.md — Daily Execution (DD-1, DD-5)

| ID | Requirement | Trace |
|----|-------------|-------|
| FR-4.1 | plan-for-the-day.md states single primary goal for the session. | DD-1 |
| FR-4.2 | plan-for-the-day.md lists 2–4 target issues pulled from EXECUTION_QUEUE with TDD protocol per task. | DD-4 |
| FR-4.3 | TDD Execution Protocol enforces: Test (Red) → Feat (Green) → Refactor (Clean) as separate commits. | AGENTS.md §6 |
| FR-4.4 | plan-for-the-day.md includes Retrospective section: What took longer, What broke, Non-goal pressure, Queue deltas, Learnings. | DD-1 |

### FR-5: docs/product/discovery-draft.md — JTBD & Acceptance (DD-1 through DD-6)

| ID | Requirement | Trace |
|----|-------------|-------|
| FR-5.1 | discovery-draft.md states JTBD: planning hierarchy for traceability and drift visibility. | DD-1 |
| FR-5.2 | discovery-draft.md names riskiest assumption: cascade maintenance vs. staleness, with validation signal. | DD-2 |
| FR-5.3 | discovery-draft.md defines measurable acceptance criterion: agent orients in ≤2 min using cascade files. | DD-3 |
| FR-5.4 | discovery-draft.md includes Test-Type Reasoning table (Unit/Integration/Contract/Acceptance/Live-system/Static). | DD-5 |
| FR-5.5 | discovery-draft.md defines Scope Boundary (In/Out) referencing VISION non-goals and existing docs. | DD-2, DD-6 |

### FR-6: docs/product/spec.md — This Document (DD-1)

| ID | Requirement | Trace |
|----|-------------|-------|
| FR-6.1 | This spec.md contains numbered functional requirements (FR-1 through FR-7) tracing to discovery-draft sections. | DD-1 |
| FR-6.2 | Each FR has sub-requirements with IDs (FR-X.Y) and trace column linking to DD-N. | DD-1 |

### FR-7: Cross-Cutting Doc Integration (DD-1, DD-6)

| ID | Requirement | Trace |
|----|-------------|-------|
| FR-7.1 | VISION.md "How This Connects" table includes all existing cross-cutting docs: ARCHITECTURE.md, KNOWN_LIMITATIONS.md, CHANGE_IMPACT_MAP.md. | DD-6 |
| FR-7.2 | VISION.md "How This Connects" table notes AI_STANCE.md, RELEASE_PROCESS.md, DEPLOYMENT_STRATEGY.md as "not yet exist — will create when process matures (see MILESTONES H2)". | DD-6 |
| FR-7.3 | VISION.md notes CONTRACTS.md does not apply (no external integration surface beyond .fawkespipe.yml). | DD-6 |

---

## Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-1 | All cascade files use Markdown with consistent front-matter (Horizon, Owner, Review Cadence). |
| NFR-2 | All cross-link tables use consistent 2-column format: `Document \| What It Answers`. |
| NFR-3 | No placeholder text — every field specific to uFawkesPipe (no copied uFawkesObs content). |
| NFR-4 | Files pass `markdownlint` (config: `.markdownlint.json`) and `yamllint` (for any YAML front-matter). |
| NFR-5 | AGENTS.md context-files table (Section 3) updated to include cascade files in priority order. |

---

## Acceptance Criteria (Binary Pass/Fail)

| AC | Criterion | Verification |
|----|-----------|--------------|
| AC-1 | `ls VISION.md MILESTONES.md EXECUTION_QUEUE.md plan-for-the-day.md` → all exist at repo root | `bash -c 'ls ...'` |
| AC-2 | `ls docs/product/discovery-draft.md docs/product/spec.md` → both exist | `bash -c 'ls ...'` |
| AC-3 | Each cascade file opens with `Horizon: X \| Owner: Y \| Review Cadence: Z` line | `head -5 <file>` |
| AC-4 | VISION.md "How This Connects" table has ≥10 rows | `grep -c '\|' VISION.md` |
| AC-5 | MILESTONES.md traceability matrix has 8 columns (one per principle) | `grep -c 'Principle' MILESTONES.md` |
| AC-6 | EXECUTION_QUEUE.md has Scope-Drift Protection table referencing all 8 VISION non-goals | `grep -c 'Non-Goal' EXECUTION_QUEUE.md` |
| AC-7 | plan-for-the-day.md has TDD protocol with 3-phase commit separation | `grep -A2 'TDD Execution Protocol' plan-for-the-day.md` |
| AC-8 | AGENTS.md Section 3 context-files table lists new cascade files in priority order | `grep -A20 'Context Files' AGENTS.md` |
| AC-9 | All files pass `make validate` (yamllint, shellcheck, markdownlint) | `make validate` |

---

## Open Questions

| # | Question | Owner | Target |
|---|----------|-------|--------|
| Q1 | Should EXECUTION_QUEUE.md be auto-generated from GitHub Issues/Project board? | Platform Engineer | H2 (M2.3) |
| Q2 | Can plan-for-the-day.md be a template instantiated daily vs. long-lived file? | Platform Engineer | H1 (M1.6) |
| Q3 | Should MILESTONES.md traceability matrix be machine-generated from FR trace tags? | Platform Engineer | H2 |