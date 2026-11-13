# Spec: uFawkesPipe v2.0.0

**Traces to:** [`intent.md`](intent.md) | **Plan:** [`plan.md`](plan.md)

## Acceptance Criteria

- **AC-PIPE-01** (suite): `build-image` is a real Cloud Native Buildpacks
  build that produces an image, or it leaves the README's features. The
  release notes explain the jump from 1.x beta to `v2.0.0`. The text and its
  verification are in the
  [suite spec](https://github.com/paruff/uFawkes.dev/blob/main/docs/ai-sdlc/suite-release/spec.md#release-4--ufawkespipe-v200).

## Design

`v2.0.0` changes no architecture: [`docs/ARCHITECTURE.md`](../../ARCHITECTURE.md)
and the ADRs stay as they are. What it adds is a stable version number for
the interfaces below.

## Interfaces

uFawkesPipe's rows in the suite's [cross-repo interface contracts](https://github.com/paruff/uFawkes.dev/blob/main/docs/ai-sdlc/suite-release/spec.md#cross-repo-interface-contracts). From `v2.0.0`, removing or renaming
anything in a "Provides" row is a **major** change.

| Contract | Role | Defined in |
|---|---|---|
| Reusable workflows: the inputs and outputs of `reusable-*.yml` | Provides, to all six other repos | `README.md`, "Reusable workflows"; each file's `workflow_call` block |
| `ufawkes-ci` CI job image | Provides, to all seven repos | `images/ci/` |
| `.fawkespipe.yml` pipeline contract | Provides, to uFawkesDevX's golden-path templates and any application repo | [`docs/pipeline-contract.md`](../../pipeline-contract.md) |
| Pipeline trigger from uFawkesDevX's Score service | Provides, to uFawkesDevX | **Not defined.** uFawkesDevX posts to a provisional `PIPELINE_WEBHOOK_URL`. This release doesn't claim it (paruff/uFawkesPipe#217) |
| DORA event ingestion | Consumes, from uFawkesObs (`notify-obs`) | uFawkesObs `docs/CONTRACTS.md` §1, mirrored here in `contracts/dora-events/` and [`docs/dora-contract.md`](../../dora-contract.md). The mirror isn't synced automatically (paruff/uFawkesPipe#218) |
| OTLP receivers | Consumes, from uFawkesObs | uFawkesObs `docs/CONTRACTS.md` §2 |
| `fawkes-space` devcontainer image | Consumes, from uFawkesAI | Pinned by digest |

## Pipeline invariants

The [suite pipeline invariants](https://github.com/paruff/uFawkes.dev/blob/main/docs/ai-sdlc/suite-release/spec.md#pipeline-invariants) apply here, with one departure:

- **PI-2:** this repo calls its own reusables at an earlier release than the
  one the other six repos pin, because a release can't pin itself.

This repo adds:

- A reusable's `ci-image` input accepts only `ghcr.io/paruff/ufawkes-ci@sha256:…`.
- `selftest-reusables.yml` runs a changed reusable from the PR itself, because callers only see it after the next release.
- A feature is claimed only after a real pipeline run shows it working (`INTENT.md`).

## Concerns

| Risk | Handling |
|---|---|
| A change to a reusable's inputs breaks six repos at once | The inputs are a "Provides" row: a major change, moved across the suite in one step by `scripts/suite-bump.sh` |
| The DORA mirror drifts from uFawkesObs | `notify-obs` is verified against a released uFawkesObs version before the tag (AC-PIPE-01) |
