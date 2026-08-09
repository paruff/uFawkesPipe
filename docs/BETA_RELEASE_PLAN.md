# Beta Release Plan — uFawkesPipe

> Audit date: 2026-08-09. Answers "what's left before we can call this beta?"

## Current state

- Tagged through `v1.2.0` (2026-07-18), but **zero GitHub Releases published** — tags exist with no release notes.
- `CHANGELOG.md` is frozen at `0.3.0`/`[Unreleased]` and never mentions any `v1.x` tag.
- 113/113 unit tests passing (`pytest tests/unit`). Integration, smoke, and acceptance suites also exist (`make test-integration|smoke|acceptance`).
- CI: Gitleaks (hard gate), Trivy (fs + image), CodeQL, SonarQube SAST, and DefectDojo ingestion are all wired into `.woodpecker.yml` and GitHub Actions.
- Docs are unusually thorough for this stage: `GOLDEN_PATH.md`, `KNOWN_LIMITATIONS.md`, `ARCHITECTURE.md`, `pipeline-contract.md`, `acceptance-criteria.md`.

## Blockers (must fix before beta)

| # | Gap | Why it blocks beta |
|---|-----|---------------------|
| B-1 | `.fawkespipe.yml` is documented and marketed in the README as *the* way app teams configure builds, but `.woodpecker.yml` never reads it (`KNOWN_LIMITATIONS.md` L-005) | This is the core value proposition. Shipping a beta where the headline feature is a no-op will burn early adopters' trust. |
| B-2 | No GitHub Release has ever been published | "Beta" needs a tagged, documented release users can point to — not just a git tag. |
| B-3 | CodeQL failing on `main` for 3 days (`Analyze (actions)` job: "not acquired by Runner of type hosted") | Infra/queue issue, not a code defect — but can't claim green CI with a red required check. |
| B-4 | 2 open Dependabot PRs (`markdownlint-cli2-action`, `hadolint-action`) | Trivial, but should merge before cutting a release branch to avoid immediately-stale action pins. |

## Cleanup (should fix, doesn't block)

| # | Gap | Fix |
|---|-----|-----|
| C-1 | Backlog issues DY-002, DY-004, DY-006, GITOPS-001 etc. are still open even though `docs/plan.md` already dispositions them (relabel/close/supersede) | Execute the disposition table in `docs/plan.md` against the live GitHub issues. |
| C-2 | `KNOWN_LIMITATIONS.md` L-002 claims `docs/GOLDEN_PATH.md` doesn't exist — it does | Mark L-002 resolved. |
| C-3 | `CHANGELOG.md` has no entries for `v1.0.0`–`v1.2.0` | Backfill from `git log`, or reset the log going forward from the beta tag. |

## Explicitly out of scope for beta

These are documented, accepted trade-offs in `KNOWN_LIMITATIONS.md` and don't need to change:
- SQLite (Woodpecker) / embedded H2 (SonarQube) — fine for single-node dev, migrate when scaling.
- No Vault/Infisical secrets backend.
- No webhook rate limiting.
- `docker.sock` mount for CNB builds.

## Action checklist

1. Merge the 2 open Dependabot PRs.
2. Investigate/fix or waive the CodeQL `actions` job (likely a self-hosted runner capacity issue — check runner pool, or drop the `actions` language matrix entry if it's not adding value).
3. Decide B-1's scope for beta: either (a) make `.woodpecker.yml` actually load `.fawkespipe.yml` fields, or (b) update the README/docs to stop presenting it as implemented and mark it "planned" — pick one and close the gap between docs and code.
4. Run the disposition table in `docs/plan.md` against the live GitHub issues (close/relabel DY-002, DY-004, DY-006, GITOPS-001, etc.).
5. Mark `KNOWN_LIMITATIONS.md` L-002 resolved.
6. Backfill or reset `CHANGELOG.md` so it matches the tag history.
7. Cut `v1.3.0-beta.1` (or next semver) and publish an actual GitHub Release with notes.

## Gate criteria (ready to tag beta when all true)

- [ ] All Dependabot PRs merged
- [ ] CI green on `main` (including CodeQL)
- [ ] B-1 resolved one way or the other (code fix or doc correction)
- [ ] `CHANGELOG.md` reflects reality
- [ ] GitHub Release published with notes
