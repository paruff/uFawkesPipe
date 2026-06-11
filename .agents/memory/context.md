# Agent Context — Shared State

> Agents read and update this file to coordinate tasks.
> Updated by orchestrator-agent before and after each task.

## Active Task

| Field              | Value |
| ------------------ | ----- |
| **Task ID**        | —     |
| **Status**         | idle  |
| **Assigned Agent** | —     |
| **Loaded Skills**  | —     |
| **Started At**     | —     |

## Recent Changes

| Timestamp | Agent | Files Changed | Summary                 |
| --------- | ----- | ------------- | ----------------------- |
| —         | —     | —             | No changes recorded yet |

## Agent Health

| Agent                  | Last Run | Status |
| ---------------------- | -------- | ------ |
| orchestrator-agent     | —        | idle   |
| pipeline-library-agent | —        | idle   |
| buildpack-agent        | —        | idle   |
| security-agent         | —        | idle   |
| observability-agent    | —        | idle   |
| docs-agent             | —        | idle   |
| smoke-test-agent       | —        | idle   |
| workflow-agent         | —        | idle   |
| review-agent           | —        | idle   |

## Notes

- Context file is manually reset by orchestrator-agent
- Agents MUST NOT write secrets or credentials here
- Agents MUST update Status to `idle` when task completes
