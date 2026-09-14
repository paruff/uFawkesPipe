# Discovery Draft — uFawkesPipe Planning Cascade Setup

> **Date:** 2026-09-14 | **Persona:** Platform Engineer | **Status:** Ready for Spec

---

## Job to Be Done (JTBD)

**When I start working on uFawkesPipe, I want a clear, nested planning hierarchy (years → months → weeks → today) so that every task traces to the north star, scope drift is visible, and retrospectives feed back into the queue — without inventing process from scratch each session.**

---

## Riskiest Assumption

> **"The 4-tier cascade (VISION → MILESTONES → EXECUTION_QUEUE → plan-for-the-day) will actually be used and maintained, not become stale documentation."**

**Why this is risky:** Planning artifacts in solo/small-team repos often rot because:
- No forcing function to update them (no sprint ceremony, no PM)
- "Just doing the work" feels faster than updating the queue
- Retrospectives are skipped when shipping pressure mounts

**Validation signal:** After 4 weeks, check: (a) EXECUTION_QUEUE.md P1/P2 items match actual work done, (b) plan-for-the-day.md retrospectives exist for ≥3 sessions, (c) MILESTONES.md status column reflects reality. If any fails → cascade is ceremonial, not operational.

---

## Measurable Acceptance Criterion

> **Given** the 4-tier cascade files exist at repo root, **when** a new session starts, **then** the agent can:
> 1. Read VISION.md → know north star, principles, non-goals, riskiest assumption
> 2. Read MILESTONES.md → know current horizon, release gates, traceability
> 3. Read EXECUTION_QUEUE.md → know P0/P1/P2 tasks with acceptance criteria
> 4. Read plan-for-the-day.md → know today's goal, TDD protocol, retrospective template
> 5. All files cross-link via "How This Connects" tables
> 6. AGENTS.md context-files table prioritizes the cascade files correctly
>
> **Measured by:** Manual verification checklist at session start (≤2 min to orient).

---

## Test-Type Reasoning

| Test Type | Applies? | Reasoning |
|-----------|----------|-----------|
| **Unit** | No | No code logic — these are Markdown planning docs |
| **Integration** | No | No component interactions to verify |
| **Contract** | Yes | AGENTS.md §3 context-files table must list new files in correct priority order (machine-checkable) |
| **Acceptance** | Yes | Manual verification: "Can a fresh agent orient in ≤2 min using only these files?" |
| **Live-system** | No | No running system involved |
| **Static analysis** | Yes | `yamllint` on any YAML front-matter; markdownlint on .md files |

---

## Scope Boundary (What This Discovery Covers)

| In Scope | Out of Scope |
|----------|--------------|
| Creating VISION, MILESTONES, EXECUTION_QUEUE, plan-for-the-day | Changing existing AGENTS.md governance rules |
| Creating docs/product/discovery-draft.md, docs/product/spec.md | Implementing any P0/P1 tasks from the queue |
| Linking cross-cutting docs in VISION.md "How This Connects" | Creating missing cross-cutting docs (AI_STANCE, RELEASE_PROCESS, DEPLOYMENT_STRATEGY) — noted as gaps |
| Updating AGENTS.md context-files priority table | Modifying compose.yaml, .woodpecker.yml, pipeline contract |

---

## Prior Art / Reference Pattern

This cascade mirrors the pattern used in:
- `paruff/uFawkesObs` (observability plane) — VISION/MILESTONES/EXECUTION_QUEUE exist
- Internal platform team conventions — "years/months/weeks/today" nesting with cross-link tables

Key difference: uFawkesPipe is pre-alpha (vs uFawkesObs beta), so non-goals list is larger and release gates are lighter.

---

## Notes

- The existing `discovery-brief.md` (2026-07-02) covers the *acceptance test suite* increment — different scope.
- This discovery covers the *planning infrastructure* increment — meta-work to make future increments traceable.
- `docs/specification.md` (v0.3) is the spec for the acceptance test suite; `docs/product/spec.md` will be the spec for the planning cascade.
