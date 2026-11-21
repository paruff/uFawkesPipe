# Plan: the parity check counts only workflows that can run

Issue: [#145](https://github.com/paruff/uFawkesPipe/issues/145)

`scripts/shift-left/check-shift-left-parity.sh` counts a `pre-commit run` line
as CI coverage only when its workflow can run: it has a trigger besides
`workflow_call`, or a workflow that can run calls it with
`uses: ./.github/workflows/<name>`, directly or through a chain.

## Verification Strategy

| Check                                                | How                                                                             |
| ---------------------------------------------------- | ------------------------------------------------------------------------------- |
| An uncalled `workflow_call`-only workflow fails      | `scripts/shift-left/test-shift-left-parity.sh`, "Workflows nothing can trigger" |
| The same workflow called from a `pull_request` one passes | the same suite                                                             |
| Quoted and chained calls count; commented-out ones and calls from dead workflows do not | the same suite                          |
| This repo's own parity is unchanged                  | `scripts/shift-left/check-shift-left-parity.sh` reports 41 of 45 hooks in CI    |
