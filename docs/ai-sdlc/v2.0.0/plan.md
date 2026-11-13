# Plan: uFawkesPipe v2.0.0

**Traces to:** [`spec.md`](spec.md) → [`intent.md`](intent.md)

This plan lists no tasks. The sequence is
[Phase 4 of the suite plan](https://github.com/paruff/uFawkes.dev/blob/main/docs/ai-sdlc/suite-release/plan.md#phase-4--pipe-20--dojo-04-gate-ac-pipe-01),
the tasks are the sub-issues of paruff/uFawkesPipe#120 on
[Project #7](https://github.com/users/paruff/projects/7), and the reusables'
own release is [`suite-pipeline-release/plan.md`](../suite-pipeline-release/plan.md).

## Verification Strategy

| Criterion | Evidence |
|---|---|
| AC-PIPE-01 | A real pipeline run on a sample repo, linked from the release notes (paruff/uFawkesPipe#123) |
| `notify-obs` | The same run, against a released uFawkesObs version, recorded in the compatibility matrix |
| Interfaces | Review of the spec's table against `README.md` and each `workflow_call` block at the release candidate |

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
