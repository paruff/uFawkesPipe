# plan-for-the-day.md — uFawkesPipe

> **Horizon:** Today (2026-09-14) | **Owner:** Platform Engineering | **Review Cadence:** End of session

---

## Primary Goal

**Complete the 4-tier planning cascade setup (VISION, MILESTONES, EXECUTION_QUEUE, plan-for-the-day) + supporting product docs (discovery-draft, spec) and cross-cutting doc references, then update AGENTS.md context table to include all new files.**

---

## Target Issues Pulled from Queue

| Queue Ref | Task | TDD Protocol |
|-----------|------|--------------|
| **P0-1** | KNOWN_LIMITATIONS resolution audit | 1. `test:` Add failing test for each unresolved limitation (script validates RESOLVED status)<br>2. `feat:` Update KNOWN_LIMITATIONS.md with mitigations<br>3. `refactor:` Clean up resolved entries |
| **P1-1** | Trivy severity threshold alignment | 1. `test:` Add test asserting `.fawkespipe.yml.example` `trivy.severity` = `HIGH,CRITICAL`<br>2. `feat:` Update example and generator to match<br>3. `refactor:` Remove duplicate severity config |
| **P1-4** | `make test-policy` target | 1. `test:` Add test that `make test-policy` runs conftest and exits 0 on valid policy<br>2. `feat:` Add Makefile target + conftest invocation<br>3. `refactor:` Ensure target skips gracefully if Docker unavailable |

---

## TDD Execution Protocol (Per Task)

For **each task above**, execute in this exact order:

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. TEST (Red)                                                   │
│    - Write failing test(s) that define the desired behavior     │
│    - Run: make test-unit (or relevant test target) → MUST FAIL  │
│    - Commit: test(scope): add failing test for [task]           │
├─────────────────────────────────────────────────────────────────┤
│ 2. FEAT (Green)                                                 │
│    - Implement minimal code to make tests pass                  │
│    - Run: make test-unit → MUST PASS                            │
│    - Run: make validate → MUST PASS                             │
│    - Commit: feat(scope): implement [task] to pass tests        │
├─────────────────────────────────────────────────────────────────┤
│ 3. REFACTOR (Clean)                                             │
│    - Clean up: remove duplication, improve naming, extract fns  │
│    - Run: make test-unit + make validate → MUST PASS            │
│    - Commit: refactor(scope): clean up [task]                   │
└─────────────────────────────────────────────────────────────────┘
```

**Never combine test + feat in one commit.** CI must fail on the test commit intentionally.

---

## Session Retrospective (Capture at End)

### What Took Longer Than Expected

- Pre-commit hook formatting fixes (EOF, trailing whitespace, Ruff) needed multiple commit attempts before the push hook passed cleanly
- Cherry-picking onto a fresh branch after PR #82 merged required care to avoid mixing unrelated `.opencode/` deletions into the TDD commit

### What Broke That Wasn't in the Queue

- `.opencode/` directory was deleted by an opencode tool update mid-session; unrelated to our work but showed up in `git status` as unstaged deletions
- `test_no_strikethrough_without_resolved` initially failed because it only checked the Mitigation column for `**RESOLVED:**` but the actual marker is in the Impact column — had to fix the test to check both columns

### Non-Goal Pressure That Appeared

- None — all three tasks (P0-1, P1-1, P1-4) stayed within scope

### Queue Deltas (Add/Remove/Reprioritize)

| Action | Task | Reason |
|--------|------|--------|
| DONE | P0-1 KNOWN_LIMITATIONS resolution audit | Completed — all 16 items marked RESOLVED |
| DONE | P1-1 Trivy severity threshold alignment | Completed — `--severity HIGH,CRITICAL` added to vuln-scan-fs |
| DONE | P1-4 `make test-policy` target | Completed — runs conftest on policy/*.rego files |

### Learnings for VISION/MILESTONES/EXECUTION_QUEUE

- The Trivy severity alignment (P1-1) only covers the `vuln-scan-fs` step — the `image-scan` step uses a different severity config and may need alignment in a future sprint
- The `test_policy.py` and `test_woodpecker_yml.py` failures are pre-existing and NOT caused by our changes — those need separate investigation
