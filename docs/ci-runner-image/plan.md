# ufawkes-ci Runner Image — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `ghcr.io/paruff/ufawkes-ci` — the Pipe-owned, digest-pinned CI image (actions-runner + docker CLI/compose + semgrep) with a dispatch-only self-hosted runner mode and a fully-local `pipe-ci` outage mode, plus the host unit, runbook, and Dojo pilot wiring.

**Architecture:** One image layered `FROM` the published `fawkes-core` digest (never rebuilt here); two entrypoints select the mode at container start. A Pipe publish workflow mirrors uFawkesAI's devsecops pipeline (buildx multi-arch → Trivy gate → cosign + attestations → digest self-tags). The host unit is a compose template with the colima socket; Dojo is the pilot consumer; the macOS-native runner is retired after the container runner proves AC3.

**Tech Stack:** Docker buildx, actions-runner v2.337.0, docker CLI (static) + compose v2, semgrep (hash-locked pip) + vendored `p/ci` ruleset, `uv`, cosign, Trivy, GitHub Actions, colima (Docker on the MBP).

**Spec:** `docs/ci-runner-image/spec.md` (approved by owner 2026-10-06, PRs #146 + #148). The plan argues from the spec — executors read both. Spec sections are cited as `spec §N` below.

**Execution note:** All Pipe work happens in `/Users/philruff/projects/github/paruff/uFawkesPipe` on one branch-per-PR (no worktree needed; sequential PRs). Dojo work happens in its repo by direct push to main (Dojo convention). Pipe main linted its own workflows since #151 — every workflow this plan touches must pass `pre-commit run --all-files` plus the repo's shift-left hooks.

---

## Global Constraints

- **Base:** `FROM ghcr.io/paruff/fawkes-core@sha256:9f442f2695aa6e6a531ae7f95d6151ffebf850085947640e2a8e55f48300d5f5f` — literal digest in `FROM` (Dependabot bumps it). Never `:latest`, never a semver tag, for builds (spec R1).
- **Hash discipline:** every downloaded artifact pinned by version + SHA-256 per arch in `images/ci/runner.lock`; verified with `sha256sum -c` at build; a mismatch **fails the build** (spec R3).
- **Manifest:** after build, `/etc/ufawkes/tools.json` = core's entries **plus** `actions-runner`, `docker-cli`, `docker-compose`, `semgrep`, `semgrep-rules` — nothing removed (spec R3). Verified by a key-superset check.
- **Trust gate:** only `workflow_dispatch` may route to `self-hosted`; never `pull_request`; the reusable pre-flight forces `ubuntu-latest` for every non-dispatch event via expression guard (spec R4).
- **Runner identity:** labels `self-hosted,pipe-ci`; `RUNNER_TOOL_CACHE=/opt/hostedtoolcache`; state under `/opt/ufawkes-runner` (`.runner`, `_work`, logs); ruleset at `/opt/ufawkes/semgrep-rules`; core's venv `/opt/ufawkes/venv` is reused, not recreated (spec R2/R6).
- **R8 loud failure:** entrypoints exit non-zero naming the cause; a check that could not run never looks green; no swallowed errors anywhere.
- **Evidence rule:** every AC needs its run URL or transcript recorded in `docs/ci-runner-image/verification-log.md` — green is only claimed for runs that executed (spec §5).
- **Process:** Pipe = branch + PR only, agents never merge; Conventional Commits ≤ 72 chars; both pre-commit stages (default **and** `--hook-stage pre-push`) pass before every push; each PR < 400 lines; new YAML carries the license header (`insert-license` hook), new shell passes `shellcheck --severity=warning` and `shfmt -i 2 -ci -bn -sr`.
- **Host specifics:** the MBP shell is zsh (no `PIPESTATUS`); Docker runs under colima (socket `~/.colima/default/docker.sock`; `/var/run/docker.sock` absent on the host); local builds are `linux/amd64` only — multi-arch happens in the publish workflow on GitHub-hosted runners.
- **semgrep offline:** `pipe-ci security` uses only the vendored ruleset — no registry downloads ever (spec §3, AC2).

## Review Focus

Failure modes the spec implies but individual happy-path tests don't cover — each pinned to its owning task:

1. A caller passes `runner: self-hosted` on a **pull_request** event → must still run `ubuntu-latest` (event guard). Pinned in Task 7.
2. `runner.sh` with missing env or a failed `config.sh` proceeds to `run.sh` silently → must exit non-zero naming the cause. Pinned in Task 3 (AC9-i/ii).
3. `pipe-ci security` reaches for the network under `--network none` → vendored ruleset must make it offline-complete. Pinned in Tasks 2 and 4 (AC2).
4. A layer rebuild drops or renames a core `tools.json` entry → superset check must fail. Pinned in Task 2.
5. A lost `runner-state` volume mid-incident → the runbook's re-register flow must work verbatim, first try. Pinned in Task 10 (AC7).

---

### Task 0: Gate — Piece 2b diagnosis (uFawkesAI nightly)

**Files:** none in Pipe; diagnosis report lands wherever systematic-debugging puts it (uFawkesAI repo or issue).
**Interfaces:** Produces: the report link recorded in `docs/ci-runner-image/verification-log.md` (AC8).

- [ ] **Step 0.1:** Invoke `superpowers:systematic-debugging` on the red `build-devsecops-images` nightly (run 37275705085, failing job `verify ai` amd64+arm64, scheduled Oct 5). Root-cause, do not patch blindly.
- [ ] **Step 0.2:** Write the diagnosis report (root cause, evidence, proposed fix as a *separate* future change).
- [ ] **Step 0.3:** Record the report link in `verification-log.md` under AC8.

**Gate scope:** this task must complete **before merging any Dependabot core-digest bump** for `images/ci/Dockerfile` — not before building the image (the pinned digest is already published and healthy).

### Task 1: `runner.lock` + Dockerfile fetch/verify stage

**Files:**
- Create: `images/ci/runner.lock`
- Create: `images/ci/Dockerfile` (stages: `FROM ghcr.io/paruff/fawkes-core@sha256:9f44…` AS base → fetch/verify stage)

**Interfaces:**
- Produces: `runner.lock` schema —
  `{"schema": 1, "tools": {"actions-runner": {"version": "2.337.0", "sha256": {"amd64": "<hex>", "arm64": "<hex>"}}, "docker-cli": {"version": "<ver>", "sha256": {"amd64": "<hex>", "arm64": "<hex>"}}, "docker-compose": {"version": "<ver>", "sha256": {"amd64": "<hex>", "arm64": "<hex>"}}, "semgrep-rules": {"version": "<rules-commit>", "sha256": {"any": "<hex>"}}}}`
- Produces: build stage pattern `ARG TARGETARCH` → URL per arch → `sha256sum -c` from the lock → artifacts under `/out/<tool>/`. Docker versions: pick latest stable at implementation time and record them; URLs: `https://download.docker.com/linux/static/stable/{x86_64,aarch64}/docker-<ver>.tgz`, `https://github.com/docker/compose/releases/download/v<ver>/docker-compose-linux-{x86_64,aarch64}`, `https://github.com/actions/runner/releases/download/v2.337.0/actions-runner-linux-{x64,arm64}-2.337.0.tar.gz`, `https://github.com/semgrep/semgrep-rules/archive/<rules-commit>.tar.gz`.
- Consumes: core image (git, curl, jq, bash already present).

- [ ] **Step 1.1:** Download each artifact for both arches (curl), record `shasum -a 256` into `runner.lock` (docker's published `.sha256` files cross-check the CLI pin). Also `curl -s https://api.github.com/repos/semgrep/semgrep-rules/commits/main -H "Accept: application/vnd.github+json" --jq .sha` → pin that commit as `semgrep-rules.version`.
- [ ] **Step 1.2:** Write `images/ci/Dockerfile`: literal-digest `FROM` (above), then a stage that `COPY`s `runner.lock`, downloads per-`TARGETARCH`, and `sha256sum -c`s every artifact. `set -euxo pipefail`; any mismatch aborts.
- [ ] **Step 1.3 (negative test):** temporarily corrupt one hash in a copy of the lock → `docker buildx build --platform linux/amd64 -t ufawkes-ci:test .` → Expected: **build fails** with the sha256 mismatch message. Restore the lock.
- [ ] **Step 1.4 (positive):** rebuild with the real lock → Expected: build succeeds.
- [ ] **Step 1.5:** `pre-commit run --files images/ci/Dockerfile images/ci/runner.lock` + `--hook-stage pre-push` variant → Passed.
- [ ] **Step 1.6:** Commit `feat(ci-image): pinned fetch/verify stage for runner and docker tooling`.

### Task 2: semgrep engine + vendored ruleset + manifest append

**Files:**
- Create: `images/ci/python/requirements.in` (`semgrep==<ver>`)
- Create: `images/ci/python/requirements.lock` (uv-generated, hashed)
- Modify: `images/ci/Dockerfile` (install semgrep into core's venv; vendor ruleset; append `tools.json` entries)

**Interfaces:**
- Consumes: `runner.lock` (semgrep-rules pin), core venv `/opt/ufawkes/venv` with `uv` on PATH.
- Produces: `semgrep` on PATH inside the image; `/opt/ufawkes/semgrep-rules/` containing the `p/ci` pack YAMLs; `/etc/ufawkes/tools.json` extended by `{actions-runner, docker-cli, docker-compose, semgrep, semgrep-rules}` via `jq` (keys merge, core entries untouched).

- [ ] **Step 2.1:** `uv pip compile --universal --python-version 3.13 --generate-hashes images/ci/python/requirements.in -o images/ci/python/requirements.lock` (same command core uses for its lock).
- [ ] **Step 2.2:** Extend the Dockerfile: `uv pip install --python /opt/ufawkes/venv --require-hashes -r requirements.lock`; extract the `ci` pack from the verified ruleset archive to `/opt/ufawkes/semgrep-rules/`; append the five entries to `tools.json` with `jq` (`.tools += {...}` → atomic `mv`).
- [ ] **Step 2.3 (manifest superset test):** `docker build` → `docker run --rm ufawkes-ci:test sh -c "jq -S '.tools | keys' /etc/ufawkes/tools.json"` → Expected: output contains **every** core key (actionlint, editorconfig-checker, gh, gitleaks, hadolint, jq, node, opencode, osv-scanner, ruff, shellcheck, shfmt, superpowers, trivy, uv, yq, zizmor) **plus** the five new keys. Any missing core key = fail (Review Focus 4).
- [ ] **Step 2.4 (offline SAST test):** `docker run --rm --network none -v "$PWD:/src" -w /src ufawkes-ci:test semgrep scan --config /opt/ufawkes/semgrep-rules --error --validate` → Expected: exit 0, no network errors (Review Focus 3).
- [ ] **Step 2.5:** Both pre-commit stages → Passed. Commit `feat(ci-image): bake semgrep engine and vendored p/ci ruleset`.

### Task 3: `entrypoints/runner.sh` (mode 1)

**Files:**
- Create: `images/ci/entrypoints/runner.sh` (installed to `/usr/local/bin/runner.sh`, mode 0755)
- Modify: `images/ci/Dockerfile` (COPY entrypoint; unpack runner tarball to `/opt/ufawkes-runner/bin`)

**Interfaces:**
- Consumes: env `RUNNER_REPO_URL`, `RUNNER_TOKEN`, `RUNNER_NAME` (required), `RUNNER_EXTRA_LABELS` (optional, default empty); runner binaries at `/opt/ufawkes-runner/bin/{config.sh,run.sh}`.
- Produces: exit behavior per R8 — missing env → exit 2 naming the variable (stderr); failed config → exit 3 after printing the config log; success → `exec run.sh` with `RUNNER_TOOL_CACHE=/opt/hostedtoolcache` exported.

- [ ] **Step 3.1:** Write `runner.sh` with `set -euo pipefail`: (1) check each required var, echo `runner.sh: missing required env: <VAR>` and `exit 2` on the first gap; (2) if `/opt/ufawkes-runner/.runner` absent → `config.sh --url "$RUNNER_REPO_URL" --token "$RUNNER_TOKEN" --name "$RUNNER_NAME" --labels "self-hosted,pipe-ci${RUNNER_EXTRA_LABELS:+,$RUNNER_EXTRA_LABELS}" --unattended --replace --work /opt/ufawkes-runner/_work`, and on failure `cat` the log, `exit 3`; (3) export `RUNNER_TOOL_CACHE=/opt/hostedtoolcache`; (4) `exec /opt/ufawkes-runner/bin/run.sh`.
- [ ] **Step 3.2 (failing tests first):** run the three negative cases against the built image and record expected failures BEFORE the entrypoint exists (mount a stub). Then implement, then re-run:
  - `docker run --rm -e RUNNER_REPO_URL=https://x -e RUNNER_NAME=x ufawkes-ci:test runner.sh` → Expected: exit 2, stderr names `RUNNER_TOKEN` (AC9-i).
  - with all env set but `RUNNER_REPO_URL=https://invalid.example.invalid` → Expected: exit 3, config log printed, `run.sh` never reached (AC9-ii).
  - `docker run --rm ufawkes-ci:test sh -c 'command -v run.sh'` never needed — assert via the two exits above.
- [ ] **Step 3.3:** `shellcheck` + `shfmt -i 2 -ci -bn -sr --diff` clean; both pre-commit stages Passed.
- [ ] **Step 3.4:** Commit `feat(ci-image): runner entrypoint with loud failure paths`.

### Task 4: `entrypoints/pipe-ci` (mode 2)

**Files:**
- Create: `images/ci/entrypoints/pipe-ci` (installed to `/usr/local/bin/pipe-ci`, 0755)
- Modify: `images/ci/Dockerfile`

**Interfaces:**
- Consumes: core toolchain on PATH; repo files at the mounted working dir (`-v "$PWD:/src" -w /src`).
- Produces: subcommands `pre-commit [--stages s1,s2]`, `pre-push [base]`, `preflight`, `lint`, `security`, `unit`, `exec <cmd…>` — each exits with the underlying tool's code verbatim; `security` = `gitleaks detect --no-banner --redact` + `trivy fs --exit-code 1 --severity HIGH,CRITICAL .` + `semgrep scan --config /opt/ufawkes/semgrep-rules --error`.

- [ ] **Step 4.1:** Write `pipe-ci` as a bash `case` dispatcher: map each subcommand to its exact command line (spec §4.4 table is the contract; `pre-push` uses `pre-commit run --from-ref "${1:-origin/main}" --to-ref HEAD`). Unknown subcommand → usage on stderr, exit 64. No `|| true`, no output swallowing.
- [ ] **Step 4.2 (negative test):** plant a file with a fake private key in a scratch checkout → `docker run --rm -v /tmp/scratch:/src -w /src ufawkes-ci:test pipe-ci security` → Expected: exit non-zero (gitleaks finds it) (AC9-iii).
- [ ] **Step 4.3 (positive offline test):** against a clean Dojo checkout — `docker run --rm --network none -v "$PWD:/src" -w /src ufawkes-ci:test pipe-ci security` → Expected: exit 0 (AC2, Review Focus 3).
- [ ] **Step 4.4:** shellcheck/shfmt clean; both stages Passed. Commit `feat(ci-image): pipe-ci local outage CLI`.

### Task 5: Image assembly + local smoke (PR A completes)

**Files:** Modify: `images/ci/Dockerfile` (COPY entrypoints, EXPOSE none, `CMD ["bash"]`).

- [ ] **Step 5.1:** Final image assembly; rebuild tag `ufawkes-ci:test`.
- [ ] **Step 5.2 (AC2 rehearsal):** in a Dojo checkout: `docker run --rm --network none -v "$PWD:/src" -w /src ufawkes-ci:test pipe-ci pre-commit` → Expected: exit 0 (baseline hooks, no network).
- [ ] **Step 5.3 (socket smoke):** `docker run --rm -v ~/.colima/default/docker.sock:/var/run/docker.sock ufawkes-ci:test pipe-ci exec docker version` → Expected: client+server output (colima daemon reachable).
- [ ] **Step 5.4:** Record all transcripts into `docs/ci-runner-image/verification-log.md` (stub file, AC2/AC9 rows). Both stages Passed.
- [ ] **Step 5.5:** Open **PR A** (image + lock + entrypoints + log stub). Confirm PR CI green; record run URL in the log.

### Task 6: Publish workflow + Dependabot docker (PR B)

**Files:**
- Create: `.github/workflows/build-ci-image.yml`
- Modify: `.github/dependabot.yml` (add `package-ecosystem: docker`, `directory: /images/ci`)

**Interfaces:**
- Consumes: `images/ci/Dockerfile`; reference structure = uFawkesAI `.github/workflows/build-devsecops-images.yml` (read it first — mirror, don't invent).
- Produces: published `ghcr.io/paruff/ufawkes-ci` with `sha256-<digest>` self-tag + `latest` (main) + `:vX.Y.Z` (release tags `v*`); cosign keyless signature + SBOM/provenance attestations; manifest-print step; Trivy gate (HIGH/CRITICAL exit 1) + SARIF; weekly re-verify schedule; `pull_request` trigger = build+scan **only, never publish**.

- [ ] **Step 6.1:** Write the workflow: triggers `workflow_dispatch`, `push` (main, paths `images/ci/**`), `pull_request` (same paths), `schedule` (weekly), release tags `v*`; permissions `contents: read, packages: write, id-token: write`; QEMU+buildx; login ghcr `GITHUB_TOKEN`; metadata tags (`type=raw,value=sha256-{{digest}}`, `latest` on main, semver on `v*`); build-push with attestations; post-push Trivy gate + SARIF; `cat /etc/ufawkes/tools.json` step; a `verify` job that runs Tasks 3–5's negative/offline tests against the pushed digest (AC9 + AC2 in CI).
- [ ] **Step 6.2:** `actionlint .github/workflows/build-ci-image.yml` → clean; both pre-commit stages Passed (workflow lint from #151 included).
- [ ] **Step 6.3:** Open **PR B**; after CI green, merge-order note: PR B merges after PR A (workflow builds the image PR A adds).
- [ ] **Step 6.4:** Commit `feat(ci): publish ufawkes-ci image with signing and gates`.

### Task 7: Pre-flight `runner` input + R4 event guard (PR C)

**Files:**
- Modify: `.github/workflows/reusable-preflight.yml` (rebase branch `feat/reusable-runner-input` @ `c366d41` onto current main; the branch is pushed but un-PR'd)

**Interfaces:**
- Produces: workflow input `runner` (string, `default: ubuntu-latest`) and the guarded expression —
  `runs-on: ${{ (github.event_name == 'workflow_dispatch' && inputs.runner) || 'ubuntu-latest' }}`
  — so any push/PR/schedule caller is forced onto `ubuntu-latest` even if it passes `runner: self-hosted` (spec R4, Review Focus 1). Zero change for existing callers (R7).

- [ ] **Step 7.1:** `git rebase origin/main` the existing branch; add the event guard expression above (replacing plain `${{ inputs.runner }}`).
- [ ] **Step 7.2:** `actionlint` + both pre-commit stages Passed.
- [ ] **Step 7.3:** Push and open **PR C** (title `feat(ci): let callers route Pre-flight to a self-hosted runner, dispatch-gated`).
- [ ] **Step 7.4 (negative proof, AC6):** after merge, from any repo calling the reusable on a `pull_request` event with `runner: self-hosted`: the run lands on `ubuntu-latest` (check job's runner label via the run page). Record in the log.
- [ ] **Step 7.5:** Commit on the branch (amended before PR): `feat(ci): dispatch-gated runner input for reusable pre-flight`.

### Task 8: Runner host unit (PR D)

**Files:**
- Create: `runner/compose.yaml` (license header — `insert-license` requires it)
- Create: `runner/.env.example`

**Interfaces:**
- Consumes: published digest of `ufawkes-ci` (PR B output); entrypoint contract from Task 3.
- Produces: service `ufawkes-ci-runner` — `image: ghcr.io/paruff/ufawkes-ci@sha256:<digest>`; `restart: unless-stopped`; `env_file: .env`; volumes `runner-state:/opt/ufawkes-runner`, `runner-toolcache:/opt/hostedtoolcache`, `runner-precommit:/root/.cache/pre-commit`; socket bind `${DOCKER_SOCKET:-/Users/philruff/.colima/default/docker.sock}:/var/run/docker.sock`; `entrypoint: /usr/local/bin/runner.sh`. `.env.example` keys: `RUNNER_REPO_URL`, `RUNNER_NAME`, `RUNNER_TOKEN`, `DOCKER_SOCKET`.

- [ ] **Step 8.1:** Write both files; `docker compose -f runner/compose.yaml config` (with a copied `.env`) validates.
- [ ] **Step 8.2:** Both pre-commit stages Passed (license header present). Commit `feat(runner): compose host unit for ufawkes-ci`; open **PR D**.

### Task 9: Runbook (PR E — docs only)

**Files:**
- Create: `docs/ci-runner-image/runbook.md`

**Interfaces:**
- Consumes: Task 8 compose file; registration-token API `gh api --method POST repos/{owner}/{repo}/actions/runners/registration-token --jq .token`; cosign verify commands (AC1).
- Produces: sections — (1) F1 incident flow (hosted runners down: dispatch with `runner=self-hosted`); (2) F2 full-outage flow (the `pipe-ci` one-liner, `--network none` variant); (3) register/start/stop/verify/update commands; (4) trust-gate hard rule restated; (5) re-register after lost `runner-state` (Review Focus 5); (6) evidence rule pointer.

- [ ] **Step 9.1:** Write the runbook with exactly the commands that Task 10 will execute (they get proven there; any that fail are fixed and re-executed — AC7 forbids untested commands).
- [ ] **Step 9.2:** Both pre-commit stages Passed. Commit `docs(ci-runner-image): operations runbook`; open **PR E**.

### Task 10: MBP swap, Dojo wiring, macOS retirement, cleanup

**Files (Dojo repo, direct pushes per its convention):**
- Modify: `uFawkesDojo/.github/workflows/pre-commit.yml` (carry the dispatch-gated `runner` input + guarded `runs-on` from `test/preflight-mbp`, minus the probe job)
- Delete: branch `test/preflight-mbp` (after carrying its wiring commit)

**Interfaces:**
- Consumes: PR B/C/D/E merged; runner registration API; launchd agent `dev.ufawkes.dojo-runner`; runner install at `/Users/philruff/actions-runner-dojo`.
- Produces: single online runner `ufawkes-dojo-linux` (labels `self-hosted,pipe-ci`); all AC3/AC4 evidence in the log; macOS runner gone.

- [ ] **Step 10.1:** Get a registration token: `gh api --method POST repos/paruff/uFawkesDojo/actions/runners/registration-token --jq .token` → into `runner/.env` (never committed).
- [ ] **Step 10.2:** `docker compose -f runner/compose.yaml --env-file runner/.env up -d`; then `gh api repos/paruff/uFawkesDojo/actions/runners --jq '.runners[] | {name, status, labels}'` → Expected: `ufawkes-dojo-linux`, `online`.
- [ ] **Step 10.3 (AC3):** dispatch each and confirm GREEN on the new runner: `gh workflow run markdown-lint.yml -f runner=self-hosted`, `gh workflow run pre-commit.yml -f runner=self-hosted` (needs Step 10.5's wiring first — order accordingly), `gh workflow run pages.yml -f runner=self-hosted` (repo: paruff/uFawkesDojo). Record run URLs.
- [ ] **Step 10.4 (AC4):** locate the checkout under `_work` and run a real stack flow through the mounted socket: `docker exec <container> bash -c 'cd /opt/ufawkes-runner/_work/<dojo>/<dojo> && pipe-ci exec make up && pipe-ci exec make init'` (or `make verify-labs` equivalent). Expected: stack comes up via colima socket. Also `pipe-ci exec docker version` transcript.
- [ ] **Step 10.5:** Dojo: push the `pre-commit.yml` dispatch wiring to main (small, direct push, both its pre-commit stages pass).
- [ ] **Step 10.6 (AC5):** after the Dojo push, confirm the push-triggered CI run stays on `ubuntu-latest` and is GREEN. Record URL.
- [ ] **Step 10.7 (AC3 negative):** `gh api repos/paruff/uFawkesDojo/actions/runners` → Expected: **no** macOS runner remains; then retire it: `cd /Users/philruff/actions-runner-dojo && ./config.sh remove --token <token>` and `launchctl bootout gui/$(id -u)/dev.ufawkes.dojo-runner` (keep the install dir; harmless). Delete `~/Library/LaunchAgents/dev.ufawkes.dojo-runner.plist`.
- [ ] **Step 10.8:** Delete Dojo branch `test/preflight-mbp` (`git push origin --delete test/preflight-mbp`).
- [ ] **Step 10.9 (Review Focus 5, AC7):** prove the runbook's lost-volume flow verbatim: `docker compose down -v` (drops `runner-state`), re-register with a fresh token using **only runbook commands**, runner back online. Record transcript.
- [ ] **Step 10.10 (AC7, update flow):** prove the runbook's update flow verbatim: `docker compose -f runner/compose.yaml pull && docker compose -f runner/compose.yaml up -d` → Expected: same-digest no-op recreate, runner back online, `_work` intact on the surviving volumes. Record transcript.

### Task 11: Verification log + final review

**Files:**
- Create/complete: `docs/ci-runner-image/verification-log.md` (AC1–AC9 rows: run URLs + transcripts)

- [ ] **Step 11.1 (AC1):** after PR B's first main run: run the runbook's `cosign verify ghcr.io/paruff/ufawkes-ci@sha256:<digest>` + `cosign verify-attestation ...` → Expected: both succeed; record output + workflow run URL. Install cosign locally if absent (`brew install cosign` or the static binary from GitHub releases — record which).
- [ ] **Step 11.2:** Assemble the full verification log (AC1–AC9, each with its evidence; AC8 = Task 0's report link).
- [ ] **Step 11.3:** Whole-branch review per `superpowers:requesting-code-review` (fresh reviewer over all five PRs + Dojo changes), then the human merges any remaining PRs (agents never merge).
- [ ] **Step 11.4:** Final commit `docs(ci-runner-image): verification log for ufawkes-ci v1`; open the log PR.

---

## Self-Review (run before handing off; fix inline)

1. **Spec coverage:** R1→Tasks 1; R2→3,4; R3→1,2,6; R4→6,7; R5→6 (multi-arch in workflow; local amd64 only); R6→8; R7→7; R8→3,4 (+AC9 CI job in 6). ACs 1–9→Tasks 5,6,7,10,11 + log. §7 sequencing→PR letters A–E + Dojo steps. OQ1→resolved (semgrep in, Task 2). No gaps.
2. **Step scan:** each step is one action with a checkable result; no TBDs.
3. **Type consistency:** env names (`RUNNER_REPO_URL/RUNNER_TOKEN/RUNNER_NAME/RUNNER_EXTRA_LABELS`), paths (`/opt/ufawkes-runner`, `/opt/hostedtoolcache`, `/opt/ufawkes/semgrep-rules`, `/usr/local/bin/runner.sh`, `/usr/local/bin/pipe-ci`), subcommand names, and the guard expression are used identically in Tasks 3,4,6,7,8,9,10.
4. **Review Focus:** all five pinned to owning tasks (7, 3, 2+4, 2, 10).
5. **Proportion:** plan ≈ spec length; code appears only where the spec pins exact commands.
