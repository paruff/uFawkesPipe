# uFawkesPipe — Implementation Plan v0.2
*Lean issues for Deepseek v4 flash implementation*

**Status:** Draft — 2026-06-23
**Sequence:** Issues are ordered by dependency. Implement in sequence.
**Branch strategy:** One branch per issue: `feat/WP-001-artifact-dirs`, etc. PRs to `main`.
**Definition of done:** `pytest tests/` passes + `yamllint compose.yaml .woodpecker.yml` clean + manual smoke step passes.

---

## Existing open issues — disposition

| Issue | Action |
|---|---|
| DY-001 README value proposition | Label `v0.2` — update README after WP-008 |
| DY-002 GitHub Actions CI | Label `v0.3` — superseded by Woodpecker self-CI; close with comment |
| DY-003 Pipeline contract explainer | Becomes `docs/pipeline-contract.md` in WP-008 |
| DY-004 QUICKSTART smoke test | Merged into WP-007 |
| DY-005 Python language pack | Label `v0.3` — language pack work after core pipeline lands |
| DY-006 Makefile targets | Merged into WP-002 |
| DY-007 GitHub Sponsors | Label `later` — not a v0.2 concern |
| GITOPS-001 GitOps standards | Label `v0.3` — depends on FluxCD work in fawkes |

---

## WP-001 · Add artifact directory init step to `.woodpecker.yml`

**Type:** chore
**Estimated effort:** 30 min
**Depends on:** nothing
**Branch:** `feat/WP-001-artifact-dirs`

### Context
The pipeline currently has no shared artifact directory structure. Scanner steps have
nowhere standard to write output, and downstream steps have no contract to read from.

### Acceptance criteria
- [ ] `.woodpecker.yml` first step is named `init`, image `alpine:3.20`
- [ ] `init` commands: `mkdir -p artifacts/security artifacts/coverage artifacts/tests`
- [ ] `tests/test_artifact_dirs.py` exists and asserts the three paths appear in `init` commands
- [ ] `pytest tests/test_artifact_dirs.py` passes

### Implementation notes
Parse `.woodpecker.yml` in the test using the `pyyaml` library (already in `tests/requirements.txt`
— verify this; if not present, add it). Assert `steps[0].name == "init"` and that
`artifacts/security` appears in the commands string.

---

## WP-002 · Add `fawkes-net` external network to `compose.yaml` and `Makefile`

**Type:** chore / infra
**Estimated effort:** 45 min
**Depends on:** nothing (can run in parallel with WP-001)
**Branch:** `feat/WP-002-fawkes-net`

### Context
Pipeline step containers must reach `defectdojo:8080` and `sonarqube:9000` by DNS name.
This requires the Woodpecker agent and all services to share a named Docker network.
Currently the stack uses the implicit `ufawkespipe_default` network, which isolates it
from other stacks.

### Acceptance criteria
- [ ] `compose.yaml` bottom section declares:
  ```yaml
  networks:
    fawkes-net:
      external: true
      name: fawkes-net
  ```
- [ ] All four services (`woodpecker-server`, `woodpecker-agent`, `sonarqube`, `portainer`)
  have `networks: [fawkes-net]`
- [ ] `woodpecker-agent` env var changed from `WOODPECKER_BACKEND_DOCKER_NETWORK=ufawkespipe_default`
  to `WOODPECKER_BACKEND_DOCKER_NETWORK=fawkes-net`
- [ ] `Makefile` has a `network` target: `docker network create fawkes-net || true`
- [ ] `Makefile` `up` target calls `make network` before `docker compose up`
- [ ] `tests/test_compose_network.py` asserts `fawkes-net` external network declared and
  agent env var is correct
- [ ] `pytest tests/test_compose_network.py` passes

### Implementation notes
Use `pyyaml` to parse `compose.yaml` in the test. Check
`parsed["networks"]["fawkes-net"]["external"] == True` and
`"WOODPECKER_BACKEND_DOCKER_NETWORK=fawkes-net"` in the agent environment list.

---

## WP-003 · Add `secrets-scan` (Gitleaks) as hard gate step

**Type:** feat / security
**Estimated effort:** 45 min
**Depends on:** WP-001
**Branch:** `feat/WP-003-secrets-scan`

### Context
There is currently no secret leak detection in the pipeline. The repo has `.gitleaks.toml`
and `.secrets.baseline` but CI does not enforce scanning. This step must be the second step
(after `init`) and must fail the pipeline if any secret is detected.

### Acceptance criteria
- [ ] Step named `secrets-scan` uses image `zricethezav/gitleaks:v8.18.2`
- [ ] Command: `gitleaks detect --source=. --report-format=json --report-path=artifacts/security/gitleaks.json --exit-code=1`
- [ ] Step appears in `.woodpecker.yml` immediately after `init`
- [ ] `.gitleaks.toml` and `.secrets.baseline` referenced in comment above the step
- [ ] `tests/test_woodpecker_yml.py` asserts `secrets-scan` is at index 1 (zero-based) in steps list
- [ ] `pytest tests/test_woodpecker_yml.py` passes

### Implementation notes
The `--exit-code=1` flag causes Gitleaks to return exit code 1 on findings, which Woodpecker
treats as step failure. Verify this flag exists in Gitleaks v8 docs before using
(it does exist in v8.x; you may want to double-check the exact flag name in the
Gitleaks v8.18 release notes).

---

## WP-004 · Add `vuln-scan-fs` and `vuln-scan-image` Trivy steps

**Type:** feat / security
**Estimated effort:** 1 hr
**Depends on:** WP-001, WP-003
**Branch:** `feat/WP-004-trivy-scan`

### Context
The current `.woodpecker.yml` has a single `security-scan` step that exits with code 1 on
HIGH/CRITICAL. The v0.2 design separates filesystem scan (runs on every push) from image
scan (runs on `main` only after build), and both write JSON artifacts for DefectDojo
rather than failing the pipeline directly.

### Acceptance criteria
- [ ] Step `vuln-scan-fs` uses `aquasec/trivy:latest` with comment explaining unpinned exception
- [ ] Command: `trivy fs --format json --output artifacts/security/trivy-repo.json --no-progress .`
- [ ] Step `vuln-scan-image` uses `aquasec/trivy:latest` with `when: branch: main`
- [ ] Command: `trivy image --format json --output artifacts/security/trivy-image.json --no-progress <image-ref>`
- [ ] Image ref uses Woodpecker built-in variables for repo name and commit SHA (see design.md §5)
- [ ] Old `security-scan` step removed
- [ ] Test `tests/test_woodpecker_yml.py` updated to assert both new step names exist
- [ ] `pytest tests/test_woodpecker_yml.py` passes

### Implementation notes
Woodpecker built-in variable for the short SHA: you will need to verify the exact variable
name in Woodpecker v3 documentation. The design uses `${CI_COMMIT_SHA:0:7}` (bash substring);
confirm this works inside Woodpecker step containers or use a separate `export` command.

---

## WP-005 · Add `upload-defectdojo` telemetry collector step

**Type:** feat / security
**Estimated effort:** 1 hr
**Depends on:** WP-002, WP-004
**Branch:** `feat/WP-005-defectdojo-upload`

### Context
Security findings from Gitleaks and Trivy currently go nowhere after the scan steps. This
step collects the three JSON artifact files and POSTs them to DefectDojo's import-scan API.
The step is non-blocking (individual upload failures are warned, not fatal).

### Acceptance criteria
- [ ] Step named `upload-defectdojo` uses `curlimages/curl:8.6.0`
- [ ] Secret `defectdojo_api_token` injected via `from_secret`
- [ ] Step only runs on `branch: main`
- [ ] Shell loop iterates over `gitleaks.json`, `trivy-repo.json`, `trivy-image.json`
- [ ] Each file is checked for existence with `[ -f "$path" ] || continue` before POSTing
- [ ] `scan_type` is correctly mapped per scanner (see design.md §2.2)
- [ ] `product_name` uses `${CI_REPO_NAME}` or equivalent Woodpecker variable
- [ ] Failed uploads print `WARN:` prefix and do not exit non-zero
- [ ] `.env.example` updated to document `DOJO_API_TOKEN` placeholder with comment

**⚠ Prerequisite (human action required before implementation):**
Verify the DefectDojo `/api/v2/import-scan/` endpoint accepts `product_name` as a form
field for auto-creating products, or whether `product_id` (integer) is required. This
depends on your DefectDojo version and configuration. Update the step accordingly.

---

## WP-006 · Add `notify-obs` deployment event step

**Type:** feat
**Estimated effort:** 30 min
**Depends on:** WP-005
**Branch:** `feat/WP-006-notify-obs`

### Context
uFawkesObs needs a deployment event to calculate DORA deployment frequency and lead time.
This stub step POSTs a structured JSON payload after a successful deploy. It is
non-blocking.

### Acceptance criteria
- [ ] Step named `notify-obs` uses `curlimages/curl:8.6.0`
- [ ] Secret `obs_webhook_url` injected via `from_secret`
- [ ] Step only runs on `branch: main`
- [ ] Payload JSON contains: `event`, `repo`, `sha`, `pipeline`, `timestamp`
- [ ] `|| echo "WARN: uFawkesObs notification failed (non-blocking)"` appended to curl command
- [ ] `.env.example` updated with `OBS_WEBHOOK_URL` placeholder and comment
- [ ] `tests/test_woodpecker_yml.py` asserts `notify-obs` step exists

**Note:** The uFawkesObs webhook receiver URL and expected payload schema must be confirmed
before this step can be integration-tested. The stub is safe to merge without a live receiver.

---

## WP-007 · Update `QUICKSTART.md` with v0.2 prerequisites and smoke test

**Type:** docs
**Estimated effort:** 45 min
**Depends on:** WP-002 (network), WP-003 (gitleaks), WP-005 (defectdojo)
**Branch:** `feat/WP-007-quickstart`

### Context
The current QUICKSTART.md does not mention `fawkes-net`, DefectDojo, or the new Woodpecker
secrets. A developer following the current guide will get a broken pipeline. Closes DY-004.

### Acceptance criteria
- [ ] Prerequisites section adds: `docker network create fawkes-net` as step 1
- [ ] Prerequisites section adds: DefectDojo reachable on `fawkes-net` at `defectdojo:8080`
  (or documents how to skip DefectDojo for local dev by setting `upload-defectdojo`
  step `when: branch: never` override)
- [ ] Secrets setup section lists all 6 required Woodpecker secrets with `woodpecker-cli secret add` commands
- [ ] Smoke test checklist added (8 steps: start stack → trigger push → verify Gitleaks output →
  verify Trivy output → verify DefectDojo entry → verify Portainer redeploy → verify OBS event →
  run `pytest tests/`)
- [ ] `make network` target documented

---

## WP-008 · Update README and add `docs/pipeline-contract.md`

**Type:** docs
**Estimated effort:** 1 hr
**Depends on:** WP-007
**Branch:** `feat/WP-008-docs`

### Context
README still says "Jenkins-based" in the GitHub description. The pipeline contract explainer
(DY-003) is missing. Closes DY-001 and DY-003.

### Acceptance criteria
- [ ] README title and description updated: remove "Jenkins-based"; replace with
  "Woodpecker CI pipeline engine with Portainer CD, SonarQube SAST, DefectDojo security
  ingestion, and Cloud Native Buildpacks"
- [ ] GitHub repo description (set via GitHub UI or `gh repo edit --description`) updated
- [ ] Pipeline stages table in README updated to reflect v0.2 12-stage sequence
- [ ] `docs/pipeline-contract.md` created with: what `.fawkespipe.yml` is, annotated
  example for each supported language, field reference table, FAQ (3–5 questions)
- [ ] README links to `docs/pipeline-contract.md`

---

## WP-009 · Full `.woodpecker.yml` replacement and test suite consolidation

**Type:** chore
**Estimated effort:** 1 hr
**Depends on:** WP-001 through WP-006 merged
**Branch:** `feat/WP-009-woodpecker-yml-final`

### Context
Issues WP-001 through WP-006 each patch `.woodpecker.yml` incrementally. This final issue
replaces the file with the canonical v0.2 version from design.md §5, ensures all tests
pass against the complete file, and removes any dead steps from the v0.1 version.

### Acceptance criteria
- [ ] `.woodpecker.yml` matches the canonical v0.2 structure in design.md §5 exactly
- [ ] Old `notify-obs` stub step (current `echo "Pipeline complete..."`) removed
- [ ] All 12 steps present in correct order: init, secrets-scan, lint-yaml, lint-shell,
  unit-tests, sast-sonarqube, vuln-scan-fs, build, vuln-scan-image, upload-defectdojo,
  deploy-portainer, notify-obs
- [ ] `yamllint .woodpecker.yml` reports zero errors
- [ ] `pytest tests/` passes with zero failures
- [ ] PR description includes: before/after step count, which open issues are closed

---

## Milestone summary

| Milestone | Issues | Target |
|---|---|---|
| **v0.2-core** | WP-001, WP-002, WP-003, WP-004 | Week 3 (per roadmap sequencing) |
| **v0.2-telemetry** | WP-005, WP-006 | Week 3 |
| **v0.2-docs** | WP-007, WP-008 | Week 4 |
| **v0.2-final** | WP-009 | Week 4 (release gate) |

---

## Notes for Deepseek implementation

1. **Parse YAML in tests with `pyyaml`**, not string matching. Pipeline step order matters and
   string matching is brittle. Example:
   ```python
   import yaml
   with open(".woodpecker.yml") as f:
       config = yaml.safe_load(f)
   steps = {s["name"]: s for s in config["steps"]}
   assert "secrets-scan" in steps
   ```

2. **Woodpecker v3 variable names:** The built-in variables follow a `CI_*` prefix pattern.
   Confirm exact names for `CI_REPO_NAME`, `CI_COMMIT_SHA`, `CI_PIPELINE_NUMBER` against
   the Woodpecker v3 documentation at https://woodpecker-ci.org/docs/usage/environment
   before using them in `.woodpecker.yml`.

3. **Do not invent DefectDojo API field names.** Use only what is specified in this plan.
   If the API call fails during smoke testing, check the DefectDojo API docs at
   `/api/v2/` (Swagger UI is available on a running DefectDojo instance).

4. **`pyyaml` vs `ruamel.yaml`:** `pyyaml` will strip YAML comments on round-trip. Tests
   that only read (not write) YAML are safe with `pyyaml`. Do not use tests to write back
   `.woodpecker.yml` — that is a human-authored file.

5. **Each issue = one PR = one branch.** Do not bundle multiple issues in one PR. The
   dependency chain is linear enough that sequential merges are fine.