# Plan: Medium and Low audit findings (AF-08 13 14)

The suite integration harness in uFawkes.dev (`tests/suite-integration`) found
these bugs. Each finding and its stated fix is in
`AUDIT_FINDINGS.md` there. This repository's share:

- AF-08: the signing step pins its image by digest, not `latest`.
- AF-13: the deployment schema copy gains `first_commit_at` and `pr_merged_at`.
- AF-14: `deploy-marker` exits non-zero without a commit SHA or pipeline URL.

## Verification Strategy

- Each finding has a harness test that asserts the correct behaviour. The test
  failed before this change and passes after it.
- `make suite-integration-test` in uFawkes.dev, run with this branch checked
  out beside the other five repositories: all tests pass, no finding
  reproduction is left.
- Pre-commit passes on this branch.
