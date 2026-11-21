# Plan: three-tier guardrails for pipeline edits

**Traces to:** [#297](https://github.com/paruff/uFawkesPipe/issues/297) | **Status:** In progress

A pipeline edit should be validated before the Woodpecker agent sees it. Cheapest tier
first: deterministic local checks, then agent context, then read-only MCP, then CI
enforcing only what the first three cannot. Work items and status live on issue #297 and
Project #7, not here.

## Approach

- Local checks run in Docker (no host installs): `woodpecker-cli lint`, and shellcheck
  over each step's `commands:` as POSIX `sh`, because steps run under `/bin/sh`.
- The same checks run in CI (`pre-commit run --all-files`, and the pipeline's own
  `lint-pipeline` steps), because pre-commit is bypassable.
- Hooks that call Docker copy files in (`docker cp`) rather than bind-mount: in CI the
  hook runs inside a job container whose `$PWD` the host daemon cannot see.

## Verification Strategy

| Check                                              | How                                                                                       |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| A bad pipeline edit is rejected                    | `tests/unit/test_make_lint_ci.py`, `test_woodpecker_lint_hook.py`: a seeded bad file exits non-zero |
| A bashism in `commands:` is rejected               | `tests/unit/test_woodpecker_shellcheck.py`: seeded `source`, `[[ ]]`, arrays fail         |
| The lint hook works where `$PWD` is not a host path | `test_woodpecker_lint_hook.py` runs it from a foreign temp directory                      |
| The real pipeline stays clean                      | The same tests run both checks over `.woodpecker.yml`; `pre-commit run --all-files`       |
| Pipeline structure holds                           | `test_woodpecker_yml.py` asserts steps source `dora-log.sh` and tag images with the short SHA |
