# Plan: release the suite pipeline once (ci-pipeline R3, R4; #165)

Authority: uFawkes.dev `docs/ai-sdlc/ci-pipeline/spec.md` (R3, R4, R7) and the goal
paruff/uFawkes.dev#178 (sub-issue 3b). This is uFawkesPipe's side: the reusables are
released under a tag, their hook stages run in `ufawkes-ci`, and the suite can move to a
new release in one step. Adoption in the seven repos is paruff/uFawkes.dev#181.

## Changes

| Item (#165) | Where | PR |
| --- | --- | --- |
| 1. Released reusables and their contract | `README.md`, release-please tags | this PR (contract); tags already cut |
| 2. Hook stages in `ufawkes-ci` | `reusable-preflight.yml` `ci-image` input; `ci-pipeline.yml` passes the digest | #176 |
| 3. Release-match check | `/etc/ufawkes/ci-base-digest` + `pipe-ci release-match` in the image; a Pre-flight step that calls it | #178, then a follow-up |
| 4. One bump for the suite | `scripts/suite-bump.sh` | this PR |

## Verification Strategy

| Check | How it is proven | Command / CI job |
| --- | --- | --- |
| Bump rewrite is correct | Unit tests: replaces the SHA and an old comment, matches either repo-name case, leaves other actions alone | `pytest tests/unit/test_suite_bump.py` |
| Bump finds the real callers | A dry run against the seven repos lists what each would change and pushes nothing | `scripts/suite-bump.sh <tag> --dry-run` |
| Bump opens PRs | Not verified by a test: exercised by the first real bump (uFawkes.dev#181) | the PRs it opens |
| Hook stages run in the image | Pipe's own Pre-flight runs both stages in the container by digest | `Pre-flight / Pre-flight Checks` on #176 (36 hooks passed) |
| A non-digest `ci-image` is rejected | The container expression needs the exact `ghcr.io/paruff/ufawkes-ci@sha256:` prefix and a first step fails otherwise. **Not run**; a caller test would show it | none yet |
| Release-match logic | Offline tests with a stub registry: match, mismatch, and each way the check cannot run (exit 67, never a pass); also run live against ghcr | `images/ci/tests/test-release-match.sh` |
| The image records its base | `verify.sh` checks the file equals the Dockerfile's `FROM` digest | `images/ci/tests/verify.sh` |
| Contract is accurate | The README's reusables and inputs are taken from each `workflow_call` block | review against `.github/workflows/reusable-*.yml` |

## Not yet done

- A stable (non-beta) release tag: #165 says to cut it only after the reusables' own tests pass.
- The Pre-flight step that calls `pipe-ci release-match`, and Pipe's `ci-image` pin moved to the
  digest that has `ci-base-digest`: both need #178 merged and published first.
