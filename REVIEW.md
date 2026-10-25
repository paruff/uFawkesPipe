# REVIEW.md

Apply the suite rules in [uFawkesAI REVIEW.md](https://github.com/paruff/uFawkesAI/blob/main/REVIEW.md):
severity, what to flag (verification, validation, security), what to skip, the
output and the board move. This file adds only what is specific to this repo.

## Checks the PR must paste

- `make validate`
- `make test`

## UI

None. Design system: [uFawkes.dev DESIGN.md](https://github.com/paruff/uFawkes.dev/blob/main/DESIGN.md).

## Repo rules

Every other suite repo calls this repo's reusable workflows (verified
2026-10-24: `main-ci-guard.yml`, `ci-pipeline.yml` and others). A change to a reusable workflow's inputs or outputs is
Important unless the PR lists the callers it checked.
