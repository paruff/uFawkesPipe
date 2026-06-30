# Model Policy — uFawkesPipe

> Model selection and cost tracking for agent invocations in this repo.
> This file is repo-specific: what works for a docs-heavy repo may not work
> for a high-volume PromQL repo. Adjust for your cost profile.

---

## Current Model Assignment

| Agent | Model | Rationale |
| ----- | ----- | --------- |
| `feature-flow` | `nvidia/deepseek-ai/deepseek-v4-flash` | Fast iteration on build code; needs strong coding but not deep reasoning |
| `review` | `nvidia/nvidia/nemotron-3-ultra-550b-a55b` | Deep reasoning for security and architecture review |
| `test` | `nvidia/deepseek-ai/deepseek-v4-flash` | Fast test generation; pre-commit context |
| `build` | `nvidia/deepseek-ai/deepseek-v4-flash` | Code generation speed |
| `general` | `nvidia/deepseek-ai/deepseek-v4-flash` | General-purpose cost balance |

## Mode Selection

- **`primary` mode** — Full reasoning, slower, more thorough. Used by: `review`, `feature-flow`'s review phases.
- **`default` mode** — Balanced speed/cost. Used by: `build`, `test`, `general`.

---

## Cost Tracking

*(To be implemented when cost visibility is needed. For now:)*

- Each agent invocation appends a structured log entry to `.agents/logs/YYYY-MM-DD.jsonl`
- The log includes `duration_ms` and `session_id` — sufficient for basic cost estimation
- For detailed token accounting, use the `token-budget` skill

---

## When to Change Model

| Trigger | Action |
| ------- | ------ |
| Build agent produces low-quality code | Switch to a stronger model temporarily, then invest in better context/skills |
| Review misses security issues | Escalate to human; consider stronger review model |
| Token costs exceed budget | Audit with `token-budget` skill; optimize context size before downgrading model |
| New model available | Test on a representative task before switching |
