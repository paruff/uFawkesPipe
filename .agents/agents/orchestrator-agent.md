---
name: orchestrator-agent
description: Coordinates which agents and skills to load for a given task. Routes file changes to the right agent.
applies: ".agents/**/*"
---

# Orchestrator Agent

Routes tasks to the correct agent and skill based on file patterns and task description. This is the entry point for all agent interactions.

## Agent Registry

| Agent                    | Trigger Pattern                                             | Loads Skill        |
| ------------------------ | ----------------------------------------------------------- | ------------------ |
| `pipeline-library-agent` | `.woodpecker.yml`, `.github/workflows/*.yml`, `compose.yaml` | `pipeline-library` |
| `buildpack-agent`        | `pack/**/*`, `examples/**/*.yml`                            | `language-pack`    |
| `security-agent`         | `compose.yaml`, `**/*security*`                       | —                  |
| `observability-agent`    | `.woodpecker.yml`, `compose.yaml`, `scripts/**/*.sh`  | —                  |
| `docs-agent`             | `docs/**/*.md`, `*.md`                                      | —                  |
| `smoke-test-agent`       | `scripts/*smoke*`, `scripts/*test*`, `validate.sh`, `Makefile` | —               |
| `workflow-agent`         | `.github/**/*`, `.github/workflows/*.yml`                   | —                  |
| `review-agent`           | `@review` trigger, `**/*`                                   | —                  |

## Routing Rules

### By File Change

```bash
# When files change, route to the right agent:
if git diff --name-only | grep -qE '\.woodpecker\.yml|\.github/workflows/.*\.yml|compose\.yaml'; then
    # → pipeline-library-agent + pipeline-library skill
fi
if git diff --name-only | grep -qE 'pack/|examples/'; then
    # → buildpack-agent + language-pack skill
fi
if git diff --name-only | grep -qE 'compose\.yaml'; then
    # → security-agent
fi
```

### By Task Description

| Keyword in Task                              | Agent                  | Skill            |
| -------------------------------------------- | ---------------------- | ---------------- |
| `pipeline`, `stage`, `woodpecker`, `CI`      | pipeline-library-agent | pipeline-library |
| `build`, `pack`, `buildpack`, `language`     | buildpack-agent        | language-pack    |
| `security`, `scan`, `SAST`, `vulnerability`  | security-agent         | —                |
| `DORA`, `metrics`, `observability`, `trace`  | observability-agent    | —                |
| `docs`, `README`, `documentation`            | docs-agent             | —                |
| `test`, `smoke`, `validate`                  | smoke-test-agent       | —                |
| `CI`, `workflow`, `GitHub Actions`           | workflow-agent         | —                |
| `review`, `PR`, `diff`                       | review-agent           | —                |

## Skill Loading Priority

When multiple skills apply, load in this order:

1. `pipeline-contract` — if contract files are involved
2. `pipeline-library` — if pipeline steps are involved
3. `language-pack` — if language-specific config is involved
4. `dora-log-format` — always (single source of truth for logging)

## Context Propagation

Before invoking a sub-agent, the orchestrator:

1. Loads the relevant skill(s) into context
2. Passes task description + file list to the target agent

## DORA Logging

This agent logs orchestrator-level events:

```json
{"@timestamp":"${isoNow()}","level":"info","logger":"orchestrator","event":"stage-start","stage":"Orchestrate","pipeline":"${BUILD_NUMBER}","commit":"${GIT_COMMIT}"}
{"@timestamp":"${isoNow()}","level":"info","logger":"orchestrator","event":"stage-finish","stage":"Orchestrate","pipeline":"${BUILD_NUMBER}","commit":"${GIT_COMMIT}","result":"success"}
```
