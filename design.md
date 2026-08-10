# Design — BETA-CLEANUP (beta release plan items 4-7)

## 1. Constraint Check

This is a docs/process chore, not a code change — there is no architecture
decision to make. The only real judgment call is: **trust
`docs/plan.md`'s disposition table verbatim, or re-verify each issue
against current repo state first?**

`docs/plan.md` was written 2026-06-23, before WP-002 through WP-009 and
PIPE-009 landed. Several of its dispositions ("Label v0.2 — update README
after WP-008") describe a *future* state that is now the *past*. Trusting
it verbatim would under-close issues that are actually done, and the
"v0.2"/"v0.3"/"later" label scheme it invents doesn't exist as real GitHub
labels in this repo (`gh label list` shows only the GitHub-default set —
no custom milestone labels were ever created). Inventing that label
taxonomy now, for 3 issues, isn't worth it (YAGNI) — a status comment
carries the same information without a label nobody else will maintain.

**Decision: re-verify each issue against live repo evidence, then close or
comment accordingly. No new labels created.**

## 2. Evidence Gathered (per issue)

| Issue | Plan.md said | Live evidence | Disposition |
| --- | --- | --- | --- |
| DY-001 (#2) README value prop | Label v0.2, update after WP-008 | README.md has one-sentence value prop, no Jenkins mention, CI badge present | **Close** |
| DY-002 (#3) GitHub Actions CI | Close, superseded by Woodpecker | `.github/workflows/ci.yml` + 8 other workflows exist and run | **Close** |
| DY-003 (#4) pipeline contract explainer | Becomes docs/pipeline-contract.md in WP-008 | `docs/pipeline-contract.md` exists, covers stages + FAQ | **Close** |
| DY-004 (#5) QUICKSTART smoke test | Merged into WP-007 | `QUICKSTART.md` has a Smoke Test section; `scripts/quickstart-smoke-test.sh` exists | **Close** |
| DY-005 (#6) Python security scanning language pack | Label v0.3 | Issue asks for `pack/python/Dockerfile` + `Jenkinsfile.template` — both obsolete post-Jenkins-removal. `examples/.fawkespipe-python-flask.yml` exists but has no bandit/safety step; SAST/dependency-scan are generic, not per-language | **Stay open, comment** — architecture moved on, needs rescoping for buildpacks-era pipeline, not closed as done |
| DY-006 (#7) Makefile targets | Merged into WP-002 | `Makefile` has `up`, `down`, `logs`, `status`, `clean`, `validate` and more | **Close** |
| DY-007 (#8) GitHub Sponsors | Label later | `.github/FUNDING.yml` exists (partial), but Sponsors profile/tiers and README "Support" section are human/business actions, not verifiable or agent-doable | **Stay open, comment** — partial progress noted |
| GITOPS-001 (#9) GitOps standards | Label v0.3 | Most repo-local criteria met (dependabot.yml, ISSUE_TEMPLATE/, FUNDING.yml, CHANGELOG.md, CONTRIBUTING.md, semantic tags, `good first issue` label exists) but `CODEOWNERS` missing, branch protection not enabled, and issue is explicitly cross-repo scope | **Stay open, comment** — most local gaps closed, remaining gaps + cross-repo scope noted |

Net: 5 close, 3 stay-open-with-status-comment. This differs from
`docs/plan.md`'s literal text (which said close DY-002/DY-004/DY-006 only)
by *also* closing DY-001 and DY-003, because the WP-008 work their
dispositions were conditioned on has since landed.

## 3. CHANGELOG Backfill Approach

Source of truth: `git log --oneline <tag1>..<tag2>` per tag boundary,
curated into Keep a Changelog `Added`/`Changed`/`Fixed`/`Removed` buckets.
Routine `chore(deps): bump ...` commits are **not** itemized individually
— Dependabot bumps are high-volume and low-signal for a changelog reader;
they're already visible in git history if needed. Everything else (feat/
fix/docs commits that describe user-visible or contributor-visible
behavior) gets a line.

The existing `[Unreleased]` section content is real work that already
happened (traced to commit `1ad503c`, the Jenkins-legacy-removal commit)
— it is *not* deleted, just re-headed as `[1.3.0-beta.1]` and merged with
the other post-`v1.2.0` commits (GitOps lifecycle gates PR #55, preflight
fix PR #59, beta release plan PR #63, PIPE-009 PR #64).

## 4. Release Sequencing Constraint

`docs/BETA_RELEASE_PLAN.md`'s gate criteria requires `CHANGELOG.md`
reflects reality *before* tagging beta. This PR is what makes that true —
so the tag/release must happen **after a human merges this PR**, not
before. feature-flow never self-merges, so Phase 5 of this run prepares
the release notes but does not execute `git tag` / `gh release create`
against unmerged content.

## 5. Impacted Components

| Component | Change |
| --- | --- |
| GitHub Issues #2-#9 | Closed with evidence comment, or commented with status (no code) |
| `docs/KNOWN_LIMITATIONS.md` | L-002 row marked resolved |
| `CHANGELOG.md` | Backfilled `v1.0.0`-`v1.2.0`, `[Unreleased]` re-headed `[1.3.0-beta.1]` |
| `docs/plan.md` | Disposition table annotated with actual resolution (so it stops being read as a live TODO) |
| PR description | Draft `v1.3.0-beta.1` release notes included for post-merge use |
