# Specification — CONSOLIDATE-SEC (merge uFawkesSec into uFawkesPipe)

## Problem Statement

uFawkesPipe (CI/CD delivery plane) and uFawkesSec (security plane) are
separate repos that already run on the same `fawkes-net` Docker network and
integrate over one hardcoded REST call (`upload-defectdojo` → `http://
defectdojo:8080`). The user has decided to consolidate them into a single
repo/product to remove that cross-repo runtime coupling and manage them as
one deployable unit going forward. Full audit and decision context: see the
audit delivered in the prior conversation turn (repo sizes, port/volume
collision check, license mismatch, stale/unshipped `policy-check` cross-repo
git-clone step).

## Requirements

- Import uFawkesSec's git history into uFawkesPipe (not a flat file copy)
  so `git blame`/`git log` on the security code survives the merge.
- Fold uFawkesSec's compose services (defectdojo, defectdojo-nginx,
  defectdojo-celery-beat, defectdojo-celery-worker, infisical,
  trivy-server, falco) into uFawkesPipe's compose files with no port/
  volume/network-name collisions.
- Wire a real `policy-check` pipeline step in `.woodpecker.yml` against the
  now-local `policy/*.rego` files, replacing the never-shipped git-clone-at-
  runtime design that CHANGELOG.md #49 claimed but `.woodpecker.yml` never
  actually contained.
- Merge uFawkesSec's test suite into `tests/unit/`, updating any assertions
  that assumed uFawkesSec was a standalone repo (e.g. `fawkes-net` as an
  *external* network — it becomes internal once merged).
- Merge docs (`policy-guide.md`, `quickstart.md`), `AGENTS.md`, and
  `.pre-commit-config.yaml` (adopt uFawkesPipe's gitleaks-only convention;
  drop uFawkesSec's duplicate `detect-secrets`/`.secrets.baseline`).
- Resolve the license mismatch: uFawkesPipe has a real Apache-2.0 LICENSE
  file; uFawkesSec's README claims MIT but has no LICENSE file at all.
  Keep Apache-2.0 (the one that actually exists) and correct the README
  claim during the docs merge.
- Update uFawkesPipe's own README ecosystem table entry for uFawkesSec to
  reflect that it's now merged in, not a separate link.

## Out of Scope (this PR)

- Any change to the `fawkes` meta-repo (`ROADMAP.md`, top-level `README.md`
  ecosystem table) — that's a separate repo, needs its own PR, flagged as a
  follow-up for the human.
- Archiving/deleting the `ufawkessec` GitHub repo — a GitHub admin action,
  human-gated, not performed by this flow.
- Live boot of the merged 11-service stack (`make up-suite`) — **no Docker
  daemon is available in this environment** (`docker ps` fails: no
  `docker.sock`). This is documented as a required manual pre-merge check
  for the human reviewer (exact command given in the PR), not silently
  skipped.
- `tests/unit/test_policy.py` (uFawkesSec's Conftest-via-Docker policy
  tests) — same Docker-unavailable constraint. Moved into the repo as-is;
  not executed this session; flagged for the human to run before merging.

## Acceptance Criteria

| ID | Criterion | test_type |
| --- | --- | --- |
| AC-01 | uFawkesSec's git history is present in uFawkesPipe via `git subtree`, then reorganized to flat homes (`config/`, `policy/`, `docs/`, `tests/unit/`) with no leftover wrapper directory | unit |
| AC-02 | `compose.yaml`/`compose.suite.yaml` contain uFawkesSec's 7 services with no port/volume/network-name collisions against existing services | unit |
| AC-03 | `.woodpecker.yml` has a `policy-check` step running Conftest against local `policy/*.rego`, positioned before `build-image` | unit |
| AC-04 | Merged `tests/unit/test_compose_yaml.py` and `tests/unit/test_workflow_validation.py` pass via `pytest` (no Docker required) | unit |
| AC-05 | `AGENTS.md`, `README.md`, `docs/ARCHITECTURE.md` reflect the merged security-plane scope; LICENSE mismatch resolved (Apache-2.0 kept, README corrected) | unit |
| AC-06 | `.pre-commit-config.yaml` has one secret scanner (gitleaks), not two | unit |
| AC-07 | Full pytest suite (`tests/unit/`) passes except the Docker-dependent `test_policy.py`, which is explicitly flagged, not silently skipped | unit |
| AC-08 | Live-system boot of the merged stack is explicitly documented as a deferred manual pre-merge step (not executed), with the exact command | live-system (deferred — see Out of Scope) |
