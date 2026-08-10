# PIPE-009 — Design: `.fawkespipe.yml` Contract Consumption

## 1. Constraint Check

Woodpecker CE (self-hosted, as deployed here) reads pipeline config one of
two ways:
1. **Repo-local file** — `.woodpecker.yml` (or `.woodpecker/*.yml`) committed
   in the repo being built. This is what `.woodpecker.yml` in *this* repo
   already does for uFawkesPipe's own CI.
2. **External config extension** — the Woodpecker server calls an HTTP
   endpoint at pipeline-start time; the endpoint returns pipeline YAML
   dynamically. Requires a new always-on service, GitHub API credentials to
   fetch the requesting repo's files, and server-side config
   (`WOODPECKER_CONFIG_SERVICE_ENDPOINT` or equivalent per Woodpecker
   version).

There is no third native mechanism — Woodpecker does not support
"include another file's YAML fields at runtime" inside a static
`.woodpecker.yml`.

## 2. Options

### Option A — External Config Service

A new long-running HTTP service, added to `compose.yaml`, that Woodpecker
calls instead of reading `.woodpecker.yml` from the app repo. The service
fetches the app repo's `.fawkespipe.yml` via the GitHub API and translates
it into pipeline YAML on the fly.

- **Pros:** Matches the README's promise most literally — app repos never
  need a `.woodpecker.yml` at all, just `.fawkespipe.yml`. Also the
  architecture GitOps work (GITOPS-001) will eventually want.
- **Cons:** New always-on service with GitHub API credentials (new attack
  surface, new secret to manage). New `compose.yaml` service — per
  `AGENTS.md` §5 this **requires asking before doing**, not just building.
  Meaningful effort: HTTP server, GitHub API client, translation logic,
  auth, deployment, tests. Disproportionate to what's needed to unblock
  beta.

### Option B — Generator Script (recommended)

A script (`scripts/generate_woodpecker_yml.py`) that reads an app repo's
`.fawkespipe.yml` and emits a `.woodpecker.yml` for that repo. App teams
run it (via `make generate-pipeline` or directly) after editing
`.fawkespipe.yml`, commit the generated file, and a CI step in *their*
generated pipeline verifies the committed `.woodpecker.yml` isn't stale
relative to their `.fawkespipe.yml` (same idea as a `gofmt -l` or
`terraform fmt -check` drift gate).

- **Pros:** Zero new services, zero new secrets, no `compose.yaml` change
  (clears the AGENTS.md ask-before gate entirely — this only touches
  `scripts/`, which agents may add to without asking). Fully unit-testable
  with plain pytest (input `.fawkespipe.yml` → assert generated YAML).
  Matches this repo's existing testing style
  (`tests/unit/test_woodpecker_yml.py` already parses/asserts YAML
  structure the same way).
- **Cons:** Not fully "zero-config" — app teams take one explicit step
  (`make generate-pipeline`) instead of the pipeline discovering
  `.fawkespipe.yml` automatically. Requires a drift-check gate to avoid the
  generated file silently diverging from the contract source of truth.

### Option C — Runtime Shell Translation in a Shared Template

Ship one generic `.woodpecker.yml` template (in `examples/`) that app repos
copy verbatim. Its steps are static (Woodpecker's DAG can't change at
runtime), but each step's first command sources a shared
`scripts/load-contract.sh`, parses `.fawkespipe.yml` with `yq`, and exits 0
immediately (no-op) if that stage is disabled — so disabled stages "run"
but do nothing.

- **Pros:** No new services, no generation step, single template file.
- **Cons:** Doesn't satisfy R1 as written — a "disabled" stage still shows
  up as an executed (skipped) step, not an absent one; harder to keep the
  template in sync across every app repo that copied it (no single source
  of truth); `app.language`-driven command selection has to be duplicated
  in shell inside the template rather than expressed once in Python/tests.

## 3. Recommendation

**Option B.** It is the only option that fits beta scope: no new
`compose.yaml` service (avoids the AGENTS.md ask-before gate on service
structure changes), fully testable offline, and directly reusable — this
repo already has the YAML-parsing pytest infrastructure
(`tests/unit/test_woodpecker_yml.py`) to test it the same way. Option A is
the better long-term architecture and should be tracked as a follow-up once
GitOps work (GITOPS-001) lands, not built now.

## 4. Impacted Components (Option B)

| Component | File | Change |
|---|---|---|
| Generator | `scripts/generate_woodpecker_yml.py` (new) | Reads `.fawkespipe.yml`, emits `.woodpecker.yml` content |
| Generator tests | `tests/unit/test_generate_woodpecker_yml.py` (new) | Unit tests: each `.fawkespipe.yml` field → expected generated step/absence |
| Makefile | `Makefile` | New `generate-pipeline` target |
| Drift check | `scripts/generate_woodpecker_yml.py` (`--check` mode) | Exits 1 if committed `.woodpecker.yml` differs from freshly generated output — used as a stage in the *generated* pipeline, not in uFawkesPipe's own `.woodpecker.yml` |
| Docs | `docs/pipeline-contract.md`, `docs/KNOWN_LIMITATIONS.md` (L-005) | Document the generate step; mark L-005 resolved |
| Migration example | `examples/.fawkespipe-python-flask.yml` + generated counterpart | Proves the contract → pipeline translation end-to-end (AGENTS.md §8 requirement) |

`uFawkesPipe`'s own `.woodpecker.yml` (this repo's self-CI) is **not**
changed — it has no `.fawkespipe.yml` and isn't an app repo (R3).

## 5. Field → Step Mapping (v1, Option B scope)

| `.fawkespipe.yml` field | Generated `.woodpecker.yml` effect |
|---|---|
| `app.language` | Selects the language-specific `lint`/`test` command from the table already documented in `docs/pipeline-contract.md` |
| `build.builder` (`cnb`\|`docker`) | Selects CNB vs. Dockerfile build step body |
| `stages.lint.enabled: false` | Lint step omitted from generated file entirely (not present, not a no-op) |
| `stages.test.enabled: false` | Test step omitted |
| `stages.sast.enabled: false` | SAST step omitted |
| `stages.dependency_scan.enabled: false` | Dependency-scan step omitted |
| `stages.image_scan.enabled: false` | Image-scan step omitted |
| `stages.push.enabled: false` | Push step omitted |
| `advanced.timeout` | Sets pipeline-level (or per-step) timeout in generated file |
| Missing/malformed `.fawkespipe.yml` | Generator exits non-zero with an actionable message (R2) |

`kubernetes:` and `notifications:` are parsed (so malformed values still
fail validation) but do not yet produce pipeline effects — logged as a
narrowed remaining gap in `docs/KNOWN_LIMITATIONS.md`, not silently
dropped.
