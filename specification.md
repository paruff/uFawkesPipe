# PIPE-004 — Fix Stale File Reference in workflow-agent.md

**Type:** fix / docs
**Branch:** `feature/pipe-004-fix-workflow-agent-stale-ref`

---

## 1. Problem

The context files table in `.agents/agents/workflow-agent.md` lists `docker-compose.yml` as a context file. The repository uses `compose.yaml`, not `docker-compose.yml`. This stale reference causes workflow-agent to reference a deprecated file.

---

## 2. Requirements

| # | Requirement | Rationale |
|---|---|---|
| F1 | Update `docker-compose.yml` to `compose.yaml` in the context files table | Fix stale reference |
| F2 | Verify no other stale references exist in the file | Completeness |

---

## 3. Acceptance Criteria

| ID | Assertion | Verification |
|----|-----------|--------------|
| AC1 | Context files table references `compose.yaml` | `grep compose.yaml .agents/agents/workflow-agent.md` |
| AC2 | No `docker-compose.yml` references remain | `grep docker-compose.yml .agents/agents/workflow-agent.md` returns empty |
| AC3 | File passes markdownlint | `pre-commit run markdownlint --files .agents/agents/workflow-agent.md` |
