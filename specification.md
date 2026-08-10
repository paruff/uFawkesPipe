# PIPE-009 — Make `.woodpecker.yml` Actually Load `.fawkespipe.yml` Fields

**Type:** feat
**Branch:** `feature/fawkespipe-contract-consumption`
**Source:** `docs/BETA_RELEASE_PLAN.md` blocker B-1 / `docs/KNOWN_LIMITATIONS.md` L-005

---

## 1. Problem

`docs/pipeline-contract.md` and the README market `.fawkespipe.yml` as *the*
interface app teams use to configure how their app is built, tested,
scanned, and deployed by uFawkesPipe. In reality, `.fawkespipe.yml` is
purely documentation — no component reads it. This repo's own
`.woodpecker.yml` is a fixed pipeline that only builds/tests/scans
**uFawkesPipe itself**; it has nothing to do with app repos, and app repos
have no way to actually get a pipeline generated from their
`.fawkespipe.yml`.

## 2. Scope

**In scope:** a mechanism by which an application repo's `.fawkespipe.yml`
fields actually determine what pipeline runs for that repo in Woodpecker —
at minimum: `app.language`, `build.builder` (cnb/docker), `stages.*.enabled`
toggles, and `advanced.timeout`.

**Out of scope (explicitly deferred, not required for this feature):**
- Kubernetes deployment stage (`kubernetes:` block — already flagged as a
  promotion path not yet implemented, per README).
- Notification delivery (`notifications:` block) — no Slack/email
  integration exists yet; parsing the field is enough, wiring delivery is
  a separate feature.
- Full field-by-field validation/schema enforcement of `.fawkespipe.yml`
  (nice-to-have, not required to prove the contract is "live").

## 3. Requirements

- R1: When an app repo with a `.fawkespipe.yml` at its root is built by
  Woodpecker via uFawkesPipe, the pipeline that actually executes must
  reflect that file's `stages.*.enabled` flags (a disabled stage does not
  run) and `app.language` / `build.builder` choice (correct
  language/builder-specific commands run).
- R2: If `.fawkespipe.yml` is missing or malformed, the pipeline must fail
  fast with a clear error — not silently fall back to a default that
  masks the misconfiguration.
- R3: This repo's own CI (`.woodpecker.yml`, which builds uFawkesPipe
  itself) is unaffected — uFawkesPipe is a platform repo, not an app repo,
  and has no `.fawkespipe.yml` of its own.
- R4: The mechanism must work within Woodpecker CE's actual capabilities
  (no invented server-side features) — see `design.md` for the chosen
  approach and rejected alternatives.
- R5: A migration example demonstrating the working contract must exist
  in `examples/` before merge (per `AGENTS.md` §8: "Pipeline contract
  changes require a migration example in `examples/`").

## 4. Acceptance Criteria

- [x] AC-01: Given an app repo with `.fawkespipe.yml` setting
      `stages.lint.enabled: false`, the generated/executed pipeline for
      that repo contains no lint step.
      Proof: `tests/unit/test_generate_woodpecker_yml.py::TestStageToggles::test_disabled_lint_stage_produces_no_lint_step`;
      end-to-end via `examples/fawkespipe-contract-migration/` (`stages.push.enabled: false` → no `push` step, `TestMigrationExample::test_disabled_push_stage_is_absent`).
- [x] AC-02: Given an app repo with `.fawkespipe.yml` setting
      `app.language: python`, the generated/executed pipeline's test step
      uses the Python test command from the contract (or the documented
      default), not a hardcoded Java command.
      Proof: `tests/unit/test_generate_woodpecker_yml.py::TestLanguageSelection`;
      end-to-end via `examples/fawkespipe-contract-migration/` (`TestMigrationExample::test_python_language_command_is_used`).
- [x] AC-03: Given an app repo with no `.fawkespipe.yml`, the pipeline
      run fails with an actionable error message (not a silent skip).
      Proof: `tests/unit/test_generate_woodpecker_yml.py::TestContractLoading::test_missing_contract_file_raises_actionable_error`,
      `TestCheckMode::test_main_exits_nonzero_on_missing_contract`.
- [x] AC-04: Given an app repo with a `.fawkespipe.yml` that fails YAML
      parsing, the pipeline run fails with an actionable error message
      identifying the parse problem.
      Proof: `tests/unit/test_generate_woodpecker_yml.py::TestContractLoading::test_malformed_yaml_raises_actionable_error`.
- [x] AC-05: `pytest tests/unit` still passes unmodified for existing
      tests, plus new unit tests covering the parsing/translation logic.
      Proof: `pytest tests/unit` — 134 passed (113 pre-existing + 21 new in
      `tests/unit/test_generate_woodpecker_yml.py`), 2026-08-10.
- [x] AC-06: `docs/KNOWN_LIMITATIONS.md` L-005 is updated to reflect the
      resolved state (or a narrower remaining gap, if scope was reduced
      during build).
      Proof: `docs/KNOWN_LIMITATIONS.md` L-005 marked "PARTIALLY RESOLVED"
      (stages/language/builder now drive the executed pipeline;
      `kubernetes:`/`notifications:` explicitly named as the remaining gap,
      matching design.md §5's scope note).

## 5. Out of Scope

- Changing `.fawkespipe.yml`'s existing field names, types, or defaults —
  this is additive/consumption work, not a contract redesign.
- Building the DefectDojo/SonarQube/Portainer integrations further than
  they already exist.
- Any change to `uFawkesPipe`'s own `.woodpecker.yml` build of itself.
