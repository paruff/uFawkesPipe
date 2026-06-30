# CI Fix Report

## Summary

**Root Cause Category:** Code

**Problem:** Pre-commit hooks with `--fix` flags (`ruff --fix`, `ruff-format`) auto-modified Python files when run in CI via `pre-commit run --all-files`. This dirtied the working tree and caused the CI pipeline to fail with exit code 1, even though the hooks successfully fixed the issues.

## Changes Made

### 1. `.github/workflows/ci.yml` — Validate job

**Before:**
```yaml
- name: Install pre-commit
  run: pip install pre-commit

- name: Run pre-commit hooks
  run: pre-commit run --all-files
```

**After:**
```yaml
- name: Install pre-commit and ruff
  run: pip install pre-commit ruff

- name: Run pre-commit hooks (non-fixing)
  run: SKIP="ruff,ruff-format,markdownlint" pre-commit run --all-files

- name: Check Python lint (read-only)
  run: ruff check .

- name: Check Python format (read-only)
  run: ruff format --check .

- name: Check Markdown (read-only)
  run: npx --yes markdownlint-cli --config .markdownlint.json .
```

### 2. `.github/workflows/reusable-preflight.yml` — Pre-flight Checks

**Before:** Same pre-commit pattern

**After:** Same four-step split (non-fixing pre-commit + ruff check + ruff format --check + markdownlint check), with all steps gated by the existing `emergency-bypass` check.

### 3. `tests/unit/test_docker_compose_validation.py` — Format fix

### 4. `tests/unit/test_jenkinsfile_validation.py` — Format fix

### 5. `tests/unit/test_k8s_validation.py` — Format fix

Three pre-existing test files that weren't ruff-formatted. These were silently auto-fixed by the old CI (which ran `ruff --fix`), then failed because the tree was dirty. Reformatted them so the new read-only CI passes cleanly.

### Design Rationale

| Concern | Before (broken) | After (fixed) |
|---------|----------------|---------------|
| CI checks Python lint | `ruff --fix` → auto-fixes then fails | `ruff check .` → reports error cleanly |
| CI checks Python format | `ruff-format` → reformats then fails | `ruff format --check .` → reports error cleanly |
| CI checks Markdown | `markdownlint --fix` → auto-fixes then fails | `markdownlint` (no `--fix`) → reports error cleanly |
| CI checks other hooks | `pre-commit run --all-files` | Same, but `ruff/ruff-format/markdownlint` skipped |
| Local dev experience | pre-commit auto-fixes | **Unchanged** — still auto-fixes on commit |

The principle: **CI validates. Local auto-fixes.**

## Validation

| Check | Result |
|-------|--------|
| `SKIP="ruff,ruff-format,markdownlint" pre-commit run --all-files` | ✅ Pass (all 11 hooks pass) |
| `ruff check .` | ✅ Pass (no lint violations) |
| `ruff format --check .` | ✅ Pass (4 files already formatted) |
| `npx markdownlint-cli --config .markdownlint.json .` | ✅ Pass (all markdown clean) |
| `python3 -m pytest tests/ -v` | ✅ 34 passed, 0 failed |
| `yamllint .github/workflows/*.yml` | ✅ Pass |

## Remaining Risks

1. **`reusable-lint.yml` uses Black instead of ruff-format** — The Static Analysis lint job runs `black --check --diff .` while pre-commit uses `ruff-format`. These formatters may disagree. This is a pre-existing inconsistency, not introduced by this fix. To fully sync, `reusable-lint.yml` should use `ruff format --check .` (matching pre-commit).

2. **Two CI workflows run overlapping checks** — `ci.yml` Validate and `ci-pipeline.yml` Pre-flight both run pre-commit and Python checks. They are redundant. This is a pre-existing design choice; not changed to avoid unnecessary pipeline redesign.

3. **Formatting-only PRs may still surface issues** — If a branch has unformatted code, the new CI will correctly fail at the format check step instead of silently fixing and then failing. This is the *desired* behavior (CI as gate, not auto-fixer).

4. **`ci-fix-report.md` had markdownlint MD022 errors** — The initial version of this report had missing blank lines around headings. This was auto-fixed by markdownlint `--fix` in CI, causing the first CI run to fail. The errors were corrected and this report now passes the read-only check. This is a good example of why CI should validate, not fix — the author didn't know the report had issues until CI ran.
