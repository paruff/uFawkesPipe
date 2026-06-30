# CI Diagnosis

| Field | Value |
|-------|-------|
| **Failure** | `Validate` job in `ci.yml` and `Pre-flight Checks` job in `ci-pipeline.yml` |
| **Location** | `.github/workflows/ci.yml:44` and `.github/workflows/reusable-preflight.yml:92` |
| **Evidence** | `pre-commit run --all-files` invokes `ruff --fix` and `ruff-format` hooks which auto-fix Python files in CI. This dirties the working tree, causing pipeline failure with exit code 1. Logs show: "Found 1 error (1 fixed, 0 remaining)" and "1 file reformatted, 4 files left unchanged". |
| **Likely Cause** | Pre-commit hooks with `--fix` flags auto-modify files when run in CI, but CI should validate (read-only) not modify. The local working tree becomes dirty after pre-commit runs, causing the step to fail. |
| **Confidence** | HIGH |
| **Proposed Fix** | In CI, skip the auto-fix Python hooks (`ruff --fix`, `ruff-format`) when running pre-commit, and run Python lint/format checks in read-only mode separately. This ensures CI validates without modifying files, while local `pre-commit install` continues to auto-fix during development. |

## Detailed Analysis

### Root Cause

Two CI workflows both run `pre-commit run --all-files`:

1. **ci.yml** (Validate job, line 44)
2. **reusable-preflight.yml** (Pre-flight Checks, line 92)

The `.pre-commit-config.yaml` defines two Python hooks that auto-modify files:

- `ruff --fix` — auto-fixes lint violations
- `ruff-format` — auto-formats Python files

When pre-commit runs in CI and these hooks modify files, the working checkout becomes dirty. Pre-commit exits with code 1 when hooks modify files (because the original intention is that hooks should validate, and modifications mean the repo wasn't clean). This causes the CI job to fail.

### The Discrepancy

The `reusable-lint.yml` already runs Python lint/format correctly in read-only mode:
- `ruff check .` (no `--fix` — exits 1 only if violations remain)
- `black --check --diff .` (read-only format check)

However, pre-commit runs the SAME checks in auto-fix mode, creating a redundant check that fails differently.
