# Plan: uFawkesPipe as the suite's shift-left hook source

**Traces to:** uFawkes.dev [`docs/ai-sdlc/shift-left/spec.md`](https://github.com/paruff/uFawkes.dev/blob/main/docs/ai-sdlc/shift-left/spec.md)
(R3, R4, R5, R9, R10) and its [plan](https://github.com/paruff/uFawkes.dev/blob/main/docs/ai-sdlc/shift-left/plan.md)
phases C1–C6 | **Status:** In progress

The shift-left tools were built and reviewed in uFawkes.dev (phases B1–B7).
Rather than copy them into six repos, where they would drift, uFawkesPipe
publishes them once: hooks through `.pre-commit-hooks.yaml`, pinned by each
repo's `rev:`, and the tools that aren't hooks through the same pinned clone,
via `scripts/shift-left/shift-left.sh`, the one file a consumer copies.

## Order of work

| Step | What                                                                                                          |
| ---- | ------------------------------------------------------------------------------------------------------------- |
| P1   | `require-tool`, the stamps, the parity check, triage, and the consumer shim; the manifest's first hooks       |
| P2   | The doctor and the agent gate (and their fault-injection tests), run through the shim                         |
| P3   | The semgrep hook: needs packaging so pre-commit can install semgrep (a dependency, so it asks first)          |
| P4   | `reusable-preflight.yml` runs every hook stage and the commit-msg hook (a change for every caller, so it asks) |
| P5   | uFawkesPipe uses its own hooks; then each suite repo switches to the shared source, one PR each               |

## Verification Strategy

| Check                                     | How                                                                                   |
| ----------------------------------------- | ------------------------------------------------------------------------------------- |
| Each tool behaves as in uFawkes.dev       | Its test suite, moved unchanged apart from paths, in `scripts/run-unit-tests.sh`      |
| The shim finds the pinned clone           | `scripts/shift-left/test-shift-left-shim.sh`: args and stdin pass through; loud fails |
| The semgrep hook installs and scans      | `try-repo` from a consumer: a seeded `run:` injection fails, the `env:` form passes |
| The hooks work from a consumer repo       | `pre-commit try-repo <this repo> <hook>` from a throwaway repo, per hook              |
| The manifest is valid                     | `pre-commit validate-manifest .pre-commit-hooks.yaml`                                 |
