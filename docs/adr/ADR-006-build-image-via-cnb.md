# ADR-006: `build-image` builds with Cloud Native Buildpacks

**Status:** Accepted, 2026-11-18 (owner decision on
[#122](https://github.com/paruff/uFawkesPipe/issues/122)).
**Traces to:** AC-PIPE-01 in [`docs/ai-sdlc/v2.0.0/spec.md`](../ai-sdlc/v2.0.0/spec.md).

## Context

`.woodpecker.yml`'s `build-image` step is a placeholder: it echoes "CNB build
would execute here" and builds nothing, yet the README lists CNB image builds
as a feature, and `generate-sbom`, `sign-image` and the later publish steps
act on an image that step never produces. AC-PIPE-01 requires either a real
CNB build or removing the claim before `v2.0.0`.

## Decision

Keep the claim and make it true. `build-image` runs `pack build` with the
builder the pipeline contract names (`build.cnb.builder`, default
`paketobuildpacks/builder:base`), and tags the image the way the later steps
already expect: `${REGISTRY_USERNAME}/${CI_REPO_NAME}:${CI_COMMIT_SHA:0:7}`.
`builder: docker` stays an alternative in the contract.

## Consequences

- The step keeps its place in the build stage, after the scans and policy
  check, on `main` only. Its image must be pinned (no `latest`), and the
  registry credentials come from Woodpecker secrets.
- Replacing the placeholder is a pipeline-step change; it needs its own PR
  (tests first) and a real run on a branch before `v2.0.0`
  ([#123](https://github.com/paruff/uFawkesPipe/issues/123) records that run).
- Until that PR merges, the README claim is not yet true, so the release
  notes must not say it is.
- Rejected alternative: drop CNB from the README and keep only the
  `docker` builder. That would leave `pack/` and `build.cnb.*` in the
  contract with nothing behind them.
