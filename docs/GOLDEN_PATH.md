# Golden Path — uFawkesPipe

> The canonical "idea → deploy" workflow for platform engineers working on uFawkesPipe.
> Follow this sequence. Deviations require documented justification.

---

## Phase 0 — Discovery & Spec

**Input:** A platform need (e.g. "add a new security scan step", "update pipeline contract")

```
1. Run discovery (15-min JTBD exercise) → discovery-brief.md
2. Extract requirements → specification.md
3. Define acceptance criteria (binary pass/fail)
4. Check governance alignment:
   - Pipeline policy (required stages, security gates)
   - K8s policy (if manifests change)
   - Template governance (naming, directory structure)
```

**Gate:** Spec must clearly state what changes and what stays the same. "Out of scope" section required.

---

## Phase 1 — Design

**Input:** specification.md

```
1. Architecture decomposition → component map
2. Interface definition → API contracts, data models, event schemas
3. Component identification → which services/modules change
4. K8s design validation → if manifests change
```

**Gate:** Design must identify **all** files that change (per the change impact map in `docs/CHANGE_IMPACT_MAP.md`).

---

## Phase 2 — Plan

**Input:** specification.md + design.md

```
1. Task decomposition → tasks.json with ordered work items
2. Dependency mapping → dependency graph
3. Skill matching → assign required skills per task
4. Risk identification → flag risky or high-effort items
```

**Gate:** Every task has acceptance criteria and a skill assignment.

---

## Phase 3 — Build

**Input:** tasks.json

```
1. Execute tasks in dependency order
2. Run local validation per task:
   - yamllint (YAML files)
   - shellcheck (Bash scripts)
   - pytest tests/ (Python tests)
   - docker compose config (compose.yaml)
   - make validate
3. Produce build-report.md
```

**Gate:** All local checks pass. No `latest` tags (except Trivy). No secrets committed.

---

## Phase 4 — Test Execution

**Input:** build-report.md

```
1. make test-unit        → unit tests (fast, always)
2. make test-integration → integration tests (requires Docker)
3. make test-smoke       → smoke tests (requires running stack, if available)
```

**Gate:** All acceptance criteria pass. Coverage thresholds met (if applicable).

---

## Phase 5 — Review

**Input:** design.md + build-report.md + test-report.md

```
Checks:
- Correctness: implementation matches requirements
- Scope: no unnecessary changes
- Architecture: follows documented patterns
- Risk: security, performance, breaking changes
```

**Gate:** APPROVED or REQUEST CHANGES.

---

## Phase 6 — Verification & Cross-Validation

**Input:** diff + build-report + test-report + review-report

```
1. Verification: evidence-based check that claims in reports are actually true
2. Cross-validation: reports are consistent with original spec and design
```

**Gate:** Both PASS before delivery prep.

---

## Phase 7 — Delivery

```
1. Commit: conventional commit format
2. Push feature branch
3. Open PR with AI-Assisted Review Block (per AGENTS.md §7)
4. CI runs automatically on push and PR
```

**Gate:** Never merge own PR. Human approval + green CI required.

---

## Phase 8 — Post-Merge

```
1. Release (if applicable) → CHANGELOG, semver tag, GitHub Release
2. Measure → DORA metrics check (via uFawkesObs)
3. Learn → retrospective, map findings to DORA AI capabilities
```

---

## Golden Path Cheat Sheet

```bash
# Quick start after a spec is ready
make validate                # Check current state
make test-unit               # Run existing tests
# ... implement changes ...
make validate                # Re-check
make test-unit               # Re-run tests
make test-integration        # Integration tests
git add -p                   # Review changes interactively
# commit, push, PR
```

## Exceptions

Any deviation from this golden path must be:
1. Documented in the PR description
2. Justified in the AI-Assisted Review Block
3. Reviewed by a human

Examples of valid exceptions: docs-only changes skip Phases 3-6; emergency fixes may compress Phases 1-2.
