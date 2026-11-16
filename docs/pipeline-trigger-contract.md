# Pipeline-trigger contract

How another suite plane starts a pipeline run here. Today the only caller is
uFawkesDevX's Score service, when a spec is created or updated. The contract is
Woodpecker's own "create pipeline" call; uFawkesPipe adds no receiver.

## Request

```text
POST http://<woodpecker-host>:8000/api/repos/<repo-id>/pipelines
Authorization: Bearer <woodpecker-api-token>
Content-Type: application/json
```

```json
{
  "branch": "main",
  "variables": {
    "SCORE_WORKLOAD": "my-workload",
    "SCORE_ACTION": "spec-updated",
    "SCORE_METADATA": "{\"version\":3}",
    "SCORE_TIMESTAMP": "2026-08-14T12:00:00.000Z"
  }
}
```

| Field | Rule |
| ----- | ---- |
| URL | `<repo-id>` is the repository's numeric id in Woodpecker (`GET /api/repos/lookup/<owner>/<repo>`) |
| Token | A Woodpecker API token ([webhook-api.md](webhook-api.md), "Authentication"); sent as a bearer token |
| `branch` | The branch to run. The caller's default is `main` |
| `message`, `workflow` | Optional Woodpecker fields; the caller doesn't send them |
| Permission | The token's user needs push access to the repository (Woodpecker's create-pipeline call checks it) |
| `variables` | Strings only. They reach the pipeline as environment variables, so a pipeline reads `SCORE_WORKLOAD` and the rest by name |

## Response

Woodpecker answers `200` with the new pipeline. A caller treats any other status
or a network error as a warning and carries on: a trigger never blocks the
caller's own work.

## Who owns what

| Side | Owns |
| ---- | ---- |
| uFawkesPipe | This request shape, and Woodpecker's version (v3) behind it |
| uFawkesDevX | The caller: `PIPELINE_WEBHOOK_URL`, `PIPELINE_WEBHOOK_TOKEN` and `PIPELINE_BRANCH` in `.env`, and the variable names |

A change to the URL shape, the auth scheme or the variable names is a breaking
change for uFawkesDevX's release. `tests/unit/test_pipeline_trigger_contract.py`
holds the example above to the rules in the table.

## Not covered yet

Nothing in this repo runs the call against a live Woodpecker server. The request
follows Woodpecker v3's API; a real run is the next check.
