# BETA-CLEANUP — Beta Release Plan Items 4-7

**Type:** chore
**Branch:** `chore/beta-release-cleanup`
**Source:** `docs/BETA_RELEASE_PLAN.md` action checklist items 4-7

---

## 1. Problem

`docs/BETA_RELEASE_PLAN.md` lists 4 remaining action-checklist items before
uFawkesPipe can be tagged beta: stale backlog issues are undispositioned
against live GitHub state, a resolved known-limitation is still marked open,
`CHANGELOG.md` has no entries for any `v1.x` tag, and no GitHub Release has
ever been published.

## 2. Scope

**In scope:**
- Reconcile `docs/plan.md`'s disposition table against the *current* state
  of each live GitHub issue (not the state assumed when the table was
  written) and close/comment/relabel accordingly.
- Mark `docs/KNOWN_LIMITATIONS.md` L-002 resolved (`docs/GOLDEN_PATH.md`
  exists).
- Backfill `CHANGELOG.md` with entries for `v1.0.0` through `v1.2.0` from
  git tag/commit history, and roll the stale `[Unreleased]` section into a
  `v1.3.0-beta.1` section.
- Prepare (not execute pre-merge) the `v1.3.0-beta.1` tag + GitHub Release.

**Out of scope:**
- Actually cutting the git tag / publishing the GitHub Release before this
  PR is merged — `docs/BETA_RELEASE_PLAN.md`'s own gate criteria requires
  "`CHANGELOG.md` reflects reality" *before* tagging, and feature-flow
  never self-merges. Tag + release happen as a follow-up once a human
  merges this PR.
- Items 1-3 of the checklist (Dependabot PRs, CodeQL fix, B-1) — already
  done in prior sessions (PIPE-009, PR #64).
- GITOPS-001's cross-repo criteria (uFawkesObs, uFawkesDORA, ufawkes.dev)
  — this repo can only speak to its own state.
- Setting up an actual GitHub Sponsors profile/tiers (DY-007) — human/
  business decision, not something to fabricate.

## 3. Requirements

- R1: Every open issue in `docs/plan.md`'s disposition table (DY-001
  through DY-007, GITOPS-001) gets a disposition action taken against the
  live repo, backed by evidence (grep/gh output), not by trusting the
  table's original assumption blindly.
- R2: `docs/KNOWN_LIMITATIONS.md` L-002 row updated to resolved state,
  matching the existing strikethrough+RESOLVED convention used elsewhere
  in that table.
- R3: `CHANGELOG.md` has one entry per existing tag (`v1.0.0`, `v1.1.0`,
  `v1.1.1`, `v1.2.0`) summarizing real merged work (curated from `git log`,
  not a raw commit dump — routine dependency bumps grouped, not itemized).
- R4: `CHANGELOG.md`'s `[Unreleased]` content is preserved (not deleted)
  but re-headed as `[1.3.0-beta.1]` with today's date and merged with the
  work landed since `v1.2.0` (GitOps lifecycle gates, PIPE-009, etc.).
- R5: A draft GitHub Release title/body for `v1.3.0-beta.1` is prepared
  and ready to publish once this PR merges.

## 4. Acceptance Criteria

- [ ] AC-01: Each of DY-001..DY-007 and GITOPS-001 has a recorded
      disposition (closed-with-comment, or left-open-with-status-comment)
      backed by a specific piece of evidence from the live repo (file
      existence, workflow existence, README content, etc.), not a blind
      copy of `docs/plan.md`'s original guess.
- [ ] AC-02: `docs/KNOWN_LIMITATIONS.md` L-002 row shows the resolved
      pattern (strikethrough limitation + **RESOLVED** + mitigation note).
- [ ] AC-03: `CHANGELOG.md` contains non-empty `Added`/`Changed`/`Fixed`
      sections for `v1.0.0`, `v1.1.0`, `v1.1.1`, and `v1.2.0`, each with a
      real date matching `git log -1 --format=%ai <tag>`.
- [ ] AC-04: `CHANGELOG.md`'s former `[Unreleased]` entries are not lost —
      every bullet that was there before this change still exists somewhere
      in the new `[1.3.0-beta.1]` section.
- [ ] AC-05: A release-notes draft exists (in the PR description or a
      scratch file) for `v1.3.0-beta.1`, ready to paste into
      `gh release create` once the PR merges.

## 5. Out of Scope

- Rewriting `docs/plan.md`'s WP-001..WP-009 issue bodies — only the
  disposition table's *live-issue actions* are executed.
- Any code change — this is a docs/process chore.
