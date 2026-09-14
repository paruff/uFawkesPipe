# Model Policy — uFawkesPipe

> Grade-based model routing for uFawkesPipe. This file is referenced from `AGENTS.md §3`.
>
> **Design principle:** Task routing uses stable *grade definitions* (which rarely change). The *current model mapping* updates frequently as models improve. When a model updates or a new one appears, only the mapping table changes.

---

## Grade Definitions

Grades are defined by minimum benchmark requirements, not specific model names. Any model meeting the thresholds qualifies for that grade.

| Grade | Name | Min SWE-bench Verified | Min Context Window | When to Use |
|-------|------|------------------------|-------------------|-------------|
| **S** | Critical | ≥90% | ≥128k | High-stakes, complex reasoning: pipeline contract changes, security policy design, architecture decisions |
| **A** | Production | ≥70% | ≥64k | Standard development: compose.yaml edits, .woodpecker.yml pipeline steps, Conftest policy changes |
| **B** | Routine | ≥50% | ≥32k | Simple tasks: YAML edits, markdown, documentation, example .fawkespipe.yml files |
| **C** | Lightweight | Any | Any | Trivial edits: label changes, typo fixes, whitespace, version bumps |
| **F** | Fallback | Free tier only | Any | Emergency: when all other providers are unavailable |

### Benchmark References

| Benchmark | What It Tests | Source | Update Frequency |
|-----------|---------------|--------|------------------|
| [SWE-bench Verified](https://www.swebench.com/) | Real GitHub bugs (500 problems) | vals.ai leaderboard | Monthly |
| [SWE-bench Pro](https://www.swebench.com/) | Harder enterprise bugs (1,865 problems) | Scale AI | Quarterly |
| [HumanEval](https://github.com/openai/human-eval) | Code generation (164 problems) | OpenAI | Static |
| [LiveCodeBench](https://livecodebench.github.io/) | Dynamic coding (contamination-resistant) | Academic | Monthly |

> **Why SWE-bench Verified?** It's the best predictor of real-world coding ability. Scores ≥90% indicate frontier reasoning; ≥70% indicates production-grade; ≥50% indicates competent for simple tasks.

---

## Current Model Mapping

> **⚠️ Update this table when models change.** The grade definitions above are stable; only this mapping updates.

| Grade | Primary Model | Provider | Fallbacks | Notes |
|-------|---------------|----------|-----------|-------|
| **S** | (configure per environment) | — | — | Use for critical paths: contract changes, security, architecture |
| **A** | (configure per environment) | — | — | Standard development: compose, pipeline, policy |
| **B** | (configure per environment) | — | — | Routine tasks: docs, examples, simple YAML |
| **C** | (configure per environment) | — | — | Trivial edits only |
| **F** | (same as C) | — | — | Emergency fallback |

### Fallback Chain

```
Grade S → Grade A → Grade B → Grade F
```

Triggers: `rate_limit`, `timeout`, `server_error`

---

## Task → Grade Routing

> **Stable — rarely changes.** This table defines which grade is required for each task type.

| Task Type | Grade | Reason |
|-----------|-------|--------|
| **Pipeline contract (.fawkespipe.yml) changes** | S | Breaking changes affect all app teams; requires careful migration design |
| **Security policy (policy/*.rego) design/review** | S | Policy-as-code violations block pipelines; frontier reasoning needed |
| **Architecture decisions (compose.yaml service structure)** | S | Cross-plane impact via CHANGE_IMPACT_MAP.md; multi-service coordination |
| **Woodpecker pipeline (.woodpecker.yml) stage changes** | S | Pipeline gate changes affect every build; DORA logging critical |
| **Docker Compose multi-service edit** | A | Multi-file coordination, known patterns |
| **Conftest policy (policy/*.rego) implementation** | A | Domain-specific Rego, needs accuracy |
| **Buildpack config (pack/) changes** | A | CNB builder/extension config, domain-specific |
| **Version upgrade (Woodpecker, SonarQube, Trivy, etc.)** | B | Single version string, but needs breaking change notes |
| **Example .fawkespipe.yml updates** | B | Must follow contract patterns |
| **Documentation (Markdown, runbooks)** | B | Text generation, cross-repo links |
| **Single YAML edit (version bump, label, port)** | C | Trivial, any model works |
| **Label changes** | C | Trivial |
| **Typo fixes** | C | Trivial |

---

## Required Issue Body Format

Every issue assigned to the coding agent **must** include this block:

```
**Grade:** [S / A / B / C]
**Task type:** [compose / pipeline / policy / pack / docs / version-bump]
**Files to edit:** [explicit list — agent must not create new files unless listed here]
**Reference file:** [path to existing config to use as pattern]
**Do not touch:** [files or services outside the scope of this issue]
**Breaking changes to check:** [version-specific migration notes if applicable]
**Acceptance criteria:**
- [ ] [measurable criterion 1]
- [ ] [measurable criterion 2]
```

---

## Escalation Rule

If rework rate for a task type exceeds **20% after 5 completed PRs** with the recommended grade:

1. **First** — improve the issue body: add file targets, reference configs, breaking change notes
2. **If still above 20%** — escalate to the next grade tier
3. **Document** the decision in this section with date and evidence

---

## Grade Update Process

When a model updates or a new model appears:

1. **Check benchmarks:** Verify the model meets grade thresholds at [swebench.com](https://www.swebench.com/) or [vals.ai](https://vals.ai/benchmarks/swebench)
2. **Update mapping:** Change only the "Current Model Mapping" table above
3. **Test:** Run 3 issues through the new model at the intended grade
4. **Validate:** Check PR revision count (target: ≤1 revision per PR)
5. **Document:** Add entry to escalation log below if grade changed

### Escalation Log

| Date | Task Type | Old Grade | New Grade | Reason | Evidence |
|------|-----------|-----------|-----------|--------|----------|
| 2026-09-14 | All | Agent-specific models | Grade-based | Initial migration from hardcoded models | — |

---

## Model Policy Enforcement

- `opencode.json` configures the fallback chain and default model
- Agent YAML files specify grades for operational agents (test, review, etc.)

---

## See Also

- `AGENTS.md` §3 — Context Files (references this file)
- `AGENTS.md` §4 — Architecture Rules (contract changes require Grade S)
- `docs/CHANGE_IMPACT_MAP.md` — Cross-plane impact of contract/compose/pipeline changes
- `docs/policy-guide.md` — Conftest policy authoring (Grade A/S task)
