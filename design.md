# PIPE-004 — Design: Fix Stale File Reference in workflow-agent.md

## 1. Impacted Components

| Component | File | Change |
|---|---|---|
| Workflow Agent | `.agents/agents/workflow-agent.md` | Update context files table: `docker-compose.yml` → `compose.yaml` |

## 2. Change Details

**Before (line 16):**
```
| 2        | `docker-compose.yml`        | Services to validate              |
```

**After:**
```
| 2        | `compose.yaml`              | Services to validate              |
```

## 3. Anti-Goals

- No structural changes to the agent file
- No changes to other agents
- No new agents or skills
