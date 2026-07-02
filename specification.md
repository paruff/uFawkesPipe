# PIPE-002 — Resolve Trivy Image Tag Policy Contradiction

**Type:** docs / test
**Depends on:** WP-009
**Branch:** `feature/pipe-002-trivy-tag-policy-exception`

---

## 1. Problem

There is a contradiction in our repository's image tagging policies:
1. `CONTRIBUTING.md` strictly forbids the use of `:latest` image tags, stating that "all versions must be pinned to a specific patch".
2. `.woodpecker.yml` uses `aquasec/trivy:latest` in both `vuln-scan-fs` and `vuln-scan-image` steps. This is a deliberate, documented exception because vulnerability scanners require the latest engine and CVE database definitions to function correctly.
3. `tests/unit/test_woodpecker_yml.py` explicitly asserts that both Trivy steps use `aquasec/trivy:latest`.

This contradiction causes confusion for contributors and tools validating policy compliance. We need to formally document this exception in `CONTRIBUTING.md` and clarify the reasoning in our test assertions.

---

## 2. Requirements

### Functional

| # | Requirement | Rationale |
|---|---|---|
| F1 | Add a formal exception block to `CONTRIBUTING.md` documenting the operational justification for keeping Trivy unpinned. | Resolve policy contradiction, clarify developer guidelines |
| F2 | Add explanatory comments to the `test_uses_trivy_latest` test methods in `tests/unit/test_woodpecker_yml.py`. | Document why the test asserts `:latest` rather than treating it as a policy violation |

### Non-Functional / Constraints

| # | Requirement | Rationale |
|---|---|---|
| NF1 | Do not pin the Trivy image tag in this issue. | Out of scope — pinning scanner images requires automatic update setups (e.g., Renovate/Dependabot) and operational workflows |
| NF2 | All existing tests must pass without any modifications to their functional assertions. | Maintain pipeline correctness and safety |

---

## 3. Acceptance Criteria

| ID | Assertion | Verification Method |
|----|-----------|---------------------|
| AC1 | `CONTRIBUTING.md` contains a formal exception section for scanner images. | Manual inspection of `CONTRIBUTING.md` |
| AC2 | The exception block explicitly mentions `aquasec/trivy:latest` and explains the operational justification (needs current CVE databases and scanner engine updates). | Manual inspection of `CONTRIBUTING.md` |
| AC3 | Comments are added to both `test_uses_trivy_latest` test methods in `tests/unit/test_woodpecker_yml.py` referencing the documented exception. | Manual inspection of `tests/unit/test_woodpecker_yml.py` |
| AC4 | No functional code or pipeline changes are made to `.woodpecker.yml`. | `git diff .woodpecker.yml` shows no changes |
| AC5 | All 110+ unit/integration/smoke/acceptance tests pass. | `python3 -m pytest tests/` passes |
