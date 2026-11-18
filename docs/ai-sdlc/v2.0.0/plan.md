# Plan: uFawkesPipe v2.0.0

**Traces to:** [`spec.md`](spec.md) → [`intent.md`](intent.md)

This plan lists no tasks. The sequence is
[Phase 4 of the suite plan](https://github.com/paruff/uFawkes.dev/blob/main/docs/ai-sdlc/suite-release/plan.md#phase-4--pipe-20--dojo-04-gate-ac-pipe-01),
the tasks are the sub-issues of paruff/uFawkesPipe#120 on
[Project #7](https://github.com/users/paruff/projects/7), and the reusables'
own release is [`suite-pipeline-release/plan.md`](../suite-pipeline-release/plan.md).
The findings of the 2026-11-13 suite audit are the sub-issues of
paruff/uFawkesPipe#223.

## Verification Strategy

| Criterion | Evidence |
|---|---|
| AC-PIPE-01 | A real pipeline run on a sample repo, linked from the release notes (paruff/uFawkesPipe#123) |
| `notify-obs` | The same run, against a released uFawkesObs version, recorded in the compatibility matrix |
| Interfaces | Review of the spec's table against `README.md` and each `workflow_call` block at the release candidate |
| AC-DORA-01 | A failed run and a successful run on a sample repo, each answered with 201 by a released uFawkesObs; the successful run's event has `first_commit_at` (paruff/uFawkesPipe#220) |
| AC-DORA-02 | A CI check that compares `contracts/dora-events/` with uFawkesObs at the pinned release, and fails on today's deployment mirror (paruff/uFawkesPipe#218) |
| AC-CONTRACT-01 | A unit test: a `.fawkespipe.yml` without a field the doc calls required makes `make generate-pipeline` fail (paruff/uFawkesPipe#221) |

**Real run on the NAS, 2026-11-18 (#220):** `python-fawkes-path` workflow run 44344109474
(on `main`, `simulate_failure=true`) sent a deployment event with `status: failed`,
`environment: test`, `first_commit_at` 2026-11-18T15:15:37Z and `pr_merged_at`
2026-11-18T15:35:27Z; Obs's `ufawkesdora-ingestion` logged `POST /event 201 Created` and
`Processed event 1 (deployment)`. Run 44344387937 (a branch, so no merged PR and no
`first_commit_at`) passed 6 tests on the NAS runner and was accepted with 201 (event 2).
Still open: a passing run on `main` whose event carries `first_commit_at`.

**Evidence so far (#220, #221):** `notify-obs`'s commands, run under `sh` against a stub
ingestion server that validates each POST against `contracts/dora-events/deployment-event.schema.json`,
got 201 for a `success` run and for a `failure` run (sent as `status: failed`); both events carried
`first_commit_at` and `pr_merged_at`. This is a local simulation: the real-Woodpecker run against a
released uFawkesObs that AC-DORA-01 requires is still open. `tests/unit/test_pipeline_contract_doc.py`
covers AC-CONTRACT-01.

### Make commands

Per [the suite's rule for `make` commands](https://github.com/paruff/uFawkes.dev/blob/main/docs/ai-sdlc/suite-release/spec.md#make-verification-commands). `make validate` here checks `compose.yaml` and the agent
definitions but doesn't run the hooks (paruff/uFawkesPipe#216); run `make pre-commit-run` as well.

| Command | Proves | Needs |
|---|---|---|
| `make pre-commit-run` | Every pre-commit hook passes on every file | Nothing |
| `make validate` | `compose.yaml` and the agent and skill definitions are valid | Docker |
| `make validate-all` | The same, plus suite mode (`compose.suite.yaml`) | Docker |
| `make test` | Unit tests pass | Nothing |
| `make test-policy` | Compose and pipeline config pass the Rego policies | Docker |
| `make test-integration` | Integration tests pass | Docker |
| `make check-pipeline` | `.woodpecker.yml` isn't stale against `.fawkespipe.yml` | Nothing |
| `make test-smoke`, `make test-acceptance` | Smoke and acceptance tests pass | `make up` first |
| `make doctor` | This clone's hooks are installed and its tools are present | Nothing |
