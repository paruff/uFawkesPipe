# Specification (v1) — uFawkes CI Runner Image (`ufawkes-ci`)

Status: **Approved by owner 2026-10-06** (reviewed on PR #146: ACs, sequencing, and the former
OQ1 all approved; OQ1 resolved **semgrep IN** — decision 7). Implementation proceeds per §7:
`plan.md` next, then the phased PRs.
Date: 2026-10-06
Owner: uFawkesPipe (image build, wiring, runbook) · Pilot consumer: uFawkesDojo
Design record: in-session design review 2026-10-06 — approaches considered: (A) extend the
uFawkesAI devsecops lineage, (B) migrate that build into Pipe, (C) new Pipe image layered on the
published core digest. **Owner chose C**; design sections §1–§5 approved same session.
Upstream lineage: uFawkesAI `docs/ai-sdlc/devsecops-image/spec.md` (R1–R5, determinism, supply
chain). This spec **adds only the runner / local-CI layer**; it does not modify that spec.
Companion files (written later, per sequencing §7): `docs/ci-runner-image/plan.md`,
`docs/ci-runner-image/runbook.md`.

---

## 1. Problem

Suite CI today assumes GitHub-hosted runners and a reachable GitHub. Two failure modes are
uncovered:

- **F1 — hosted runners degraded, platform up.** Workflows must be able to route to a
  self-hosted runner on demand (dispatch only).
- **F2 — GitHub entirely down.** Every repo must be able to run its pre-commit / pre-push /
  pre-flight / security checks fully offline, from one image, with no GitHub dependency.

What already exists: `ghcr.io/paruff/fawkes-core` — the specced, signed, deterministic DevSecOps
toolchain (spec R1: "one image, three consumers: local pre-commit, devcontainer, CI jobs";
AC-3 already requires a `--network none` offline pass). What is missing, and is this spec's
scope: the **actions-runner layer**, the **`pipe-ci` local entrypoint**, the **runner host unit**
(compose + volumes + socket), the **publish workflow**, the **runbook**, and **Pipe-side wiring**.

Why not a native macOS runner (evidence, session 2026-10-05/06): `actions/setup-python` hardcodes
`/Users/runner/hostedtoolcache` (upstream issues #974/#914) **and** runs `sudo installer -pkg`
without a TTY; `pages` needed GNU tar, and `ftp.gnu.org` is unreachable from this host (Tier-3
source build failed). Native macOS runners are **retired** (owner decision).

## 2. Requirements

| # | Requirement |
|---|-------------|
| **R1** | **Layered, not forked.** `FROM ghcr.io/paruff/fawkes-core@sha256:…`, digest pinned in `FROM` itself so Dependabot's docker updater bumps it. Never `:latest`, never a semver tag, for builds. Initial pin: `sha256:9f442f2695aa6e6a531ae7f95d6151ffebf850085947640e2a8e55f48300d5f5` (= core tag `2.0.0-rc.3`). |
| **R2** | **Two modes, one image.** Mode 1: runner entrypoint — config-on-first-boot, `RUNNER_TOOL_CACHE=/opt/hostedtoolcache`, state on volumes so restarts need no token. Mode 2: `pipe-ci <flow>` subcommands, runnable as `docker run --rm -v "$PWD:/src" -w /src … pipe-ci <flow>`, including with `--network none`. |
| **R3** | **Determinism & supply chain.** Runner tarball and docker CLI/compose pinned by version **and** SHA-256 per arch in `images/ci/runner.lock` (same discipline as core's `tools.lock.json`); **every download is verified against those hashes at build time (`sha256sum -c`) and a mismatch fails the build** — pinning without verification is not enough. The layer **appends its entries (actions-runner, docker CLI, compose) to core's `/etc/ufawkes/tools.json`** so the one-manifest guarantee (devsecops AC1) survives the layer: manifest = core's manifest + our entries, nothing removed. Publish workflow mirrors the devsecops one: buildx multi-arch, Trivy gate, cosign keyless + SBOM + provenance attestations, weekly re-verify, `sha256-<digest>` self-tag. |
| **R4** | **Suite wiring compatibility + trust gate.** Runner labels include `self-hosted` (so existing dispatch input values match unchanged) plus `pipe-ci`. **Only `workflow_dispatch` may route jobs to this runner — never `pull_request`; push/PR/schedule stay GitHub-hosted.** The gate is **enforced inside the workflows themselves, not only at callers**: the reusable pre-flight must ignore a non-default `runner` input unless `github.event_name == 'workflow_dispatch'`, so no caller can accidentally route a PR event to self-hosted. `container:` adoption of hosted jobs (devsecops track) must stay an open, non-conflicting path. |
| **R5** | **Multi-arch** amd64 + arm64 at build time (core is multi-arch; runner supports both). Runtime verification in this phase is amd64 (MBP is Intel). |
| **R6** | **Host unit.** A compose template with documented per-host socket endpoint (on the MBP: colima's `~/.colima/default/docker.sock`), named volumes for runner state, tool cache, and pre-commit cache; first-boot / verify / update flows documented and copy-paste tested. |
| **R7** | **No behavior change for existing callers.** The reusable pre-flight gains a `runner` input defaulting to `ubuntu-latest`; default-path callers see no difference. |
| **R8** | **Loud failure.** Entrypoints never swallow errors and never report ready/passed when they did not run. A runner that cannot configure exits non-zero with the log line that explains why (suite rule: a check that could not run must never look green). |

## 3. Tool set

**Inherited from core** (versions live in core's `tools.lock.json` / `requirements.lock` — not
re-pinned here):

- Pre-commit & baseline: `pre-commit 4.6.2`, `pre-commit-hooks`, `yamllint`, `detect-secrets`,
  `ruff`, `ruff-format`, `shellcheck`, `hadolint`, `actionlint`, `markdownlint-cli2`,
  `trailing-whitespace` / `EOF` / `check-yaml` / `check-json` / `check-added-large-files` family,
  `gitleaks`, `detect-private-key`.
- Security scanners (the SAST/scanning inventory you asked for): **trivy** (vuln + misconfig),
  **osv-scanner**, **gitleaks** + **detect-secrets** (secrets), **zizmor** (GitHub Actions SAST),
  **hadolint** (Dockerfile), **shellcheck** (bash), **ruff** (Python).
- Platform: `bash`, `git`, `gh`, `jq`, `yq`, `make`, `python3` + `uv` venv at
  `/opt/ufawkes/venv` (pre-commit on `PATH`), `node`, `actionlint`, `editorconfig-checker`,
  `shfmt`, `codetools` as shipped by core.
- Core ships `/opt/ufawkes/pre-commit/baseline.yaml` (`language: system` hooks — runnable
  offline by construction). Repo remote-rev hook envs are **not** pre-baked (core decision
  AC-AI-09): they download once into the pre-commit cache volume on first online run.

**Added by this layer:**

| Tool | Pinning |
|---|---|
| `actions-runner` (v2.337.0 or newer current, linux-x64 + linux-arm64 tarballs) | version + per-arch SHA-256 in `runner.lock` |
| docker CLI (static) + compose v2 plugin | version + SHA-256 in `runner.lock` (exact source chosen in plan; snapshot-apt equivalent acceptable if equally pinned) |
| **semgrep** engine | version + hash-locked pip install into the layer (same discipline as core's `requirements.lock`: `uv pip install --require-hashes`) |
| **semgrep ruleset** (vendored — the `p/ci` pack Pipe's pre-push hook already uses) | pinned source commit + archive SHA-256, installed to `/opt/ufawkes/semgrep-rules/` so `pipe-ci security` is offline-capable |

**Divergence from core, deliberate:** core excludes semgrep (245 MB engine; its comment says it
"only serves CI" and installs it with pipx at job time). This layer **is** the CI image, so the
exclusion's premise inverts here (decision 7, §8). The general-purpose core image is untouched.

## 4. Design

### 4.1 Repository layout (uFawkesPipe)

```
images/ci/Dockerfile                # FROM ghcr.io/paruff/fawkes-core@sha256:… AS core
images/ci/runner.lock               # runner + docker CLI/compose versions & SHA-256s
images/ci/entrypoints/runner.sh     # mode 1: config-on-first-boot → run.sh
images/ci/entrypoints/pipe-ci       # mode 2: local outage CLI
runner/compose.yaml                 # host unit template (R6) — needs a license header
                                    # (Pipe insert-license hook covers *.yaml, excl. .github/)
runner/.env.example                 # RUNNER_REPO_URL / RUNNER_NAME / RUNNER_TOKEN / socket path
.github/workflows/build-ci-image.yml
.github/dependabot.yml              # + package-ecosystem: docker (file currently covers
                                    # github-actions + pre-commit only)
docs/ci-runner-image/spec.md        # this file
docs/ci-runner-image/plan.md        # phase 2
docs/ci-runner-image/runbook.md     # incident + ops (phase 3)
```

New files must satisfy Pipe's pre-commit gates: `shellcheck --severity=warning` and
`shfmt -i 2 -ci -bn -sr -w` on the entrypoints, license header on `runner/compose.yaml`;
both pre-commit stages (default + `--hook-stage pre-push`) pass on every PR.

### 4.2 Build & publish flow

After a PR merges to `main` touching `images/ci/**` (Pipe is PR-only — no direct trunk pushes):
buildx multi-arch → hash-verification of every locked download → Trivy gate → manifest print
(`cat /etc/ufawkes/tools.json` in the build log: core's entries **plus** the layer's, nothing
removed — R3) → cosign sign (+ SBOM, provenance attestations) → push `ghcr.io/paruff/ufawkes-ci`
with tags `sha256-<digest>` (self-tag, consumers pin this) and `latest`; release tags `v*`
additionally publish `:vX.Y.Z` via Pipe's existing release-please. Weekly scheduled run
re-builds, re-scans, re-verifies (drift + CVE watch). Consumers pin the digest, never `latest`.

### 4.3 Mode 1 — runner entrypoint (`runner.sh`)

1. If `RUNNER_REPO_URL` / `RUNNER_TOKEN` / `RUNNER_NAME` missing → fail fast, non-zero, naming
   the missing variable (R8).
2. If `runner-state` volume has no `.runner` → `config.sh --url … --token … --name … --labels
   "self-hosted,pipe-ci" --unattended --replace --work /opt/ufawkes-runner/_work`; on failure,
   print the config log and exit non-zero — **never proceed to `run.sh` unconfigured**.
3. Export `RUNNER_TOOL_CACHE=/opt/hostedtoolcache` (toolcache volume), then `exec run.sh`.
4. Registration token is only needed at first config (expires in 1 h). State persists in the
   volume, so ordinary restarts/recreates reuse `.runner`; token loss = re-register (runbook).

### 4.4 Mode 2 — `pipe-ci` local outage CLI

Thin wrappers over the preinstalled toolchain, all run from the mounted workspace, all propagating
exit codes verbatim (R8):

| Subcommand | Contract |
|---|---|
| `pipe-ci pre-commit [--stages s1,s2]` | `pre-commit run --all-files` for the given stages (default: repo default stages) |
| `pipe-ci pre-push [base]` | pre-commit over the changed range (`--from-ref <base> --to-ref HEAD`, default `origin/main`), mirroring the pre-push hook |
| `pipe-ci preflight` | the repo's required pre-flight stages + `commit-msg` check via the workspace's own scripts |
| `pipe-ci lint` / `pipe-ci security` | lint stage subset / `gitleaks` + `trivy fs .` + `semgrep scan --config /opt/ufawkes/semgrep-rules --error` over the workspace (local ruleset → runs offline) |
| `pipe-ci unit` | passthrough to the repo's test entrypoint (`make test` etc.), documented per-repo |
| `pipe-ci exec <cmd…>` | run any command inside the image environment (escape hatch, e.g. `make verify-labs`) |

Full outage one-liner (runbook): `docker run --rm -v "$PWD:/src" -w /src ghcr.io/paruff/ufawkes-ci@sha256:… pipe-ci preflight`.

### 4.5 Host unit (`runner/compose.yaml`)

Image digest-pinned; `restart: unless-stopped`; env from `.env` (`RUNNER_REPO_URL`, `RUNNER_NAME`,
`RUNNER_TOKEN` — first boot only); named volumes `runner-state` (`/opt/ufawkes-runner`: `.runner`,
`_work`, logs), `toolcache` (`/opt/hostedtoolcache`), `precommit-cache` (`/root/.cache/pre-commit`);
socket mount `type: bind` with the source resolved per host — **MBP: `~/.colima/default/docker.sock`
→ `/var/run/docker.sock`** (host `/var/run/docker.sock` does not exist under colima; documented, not
assumed). Container runs as root in-container (normal for containerized runners; mitigated by R4
trust gate + dispatch-only reachability).

### 4.6 Suite wiring

- **Consumer recipe** (Dojo already has it): `workflow_dispatch` choice input `runner`
  (`ubuntu-latest` default, `self-hosted` option) + event-guarded `runs-on` expression. The label
  `self-hosted` matches the container runner, so swapping implementations needs **zero workflow
  changes** — only the runner registration changes.
- **Pre-flight**: land the pushed branch `feat/reusable-runner-input` (`c366d41`) as PR —
  `runs-on: ${{ inputs.runner }}`, `default: ubuntu-latest` (R7), **plus the R4 event guard**:
  the reusable workflow may only honor a non-default `runner` when
  `github.event_name == 'workflow_dispatch'` (any other event forces `ubuntu-latest`), so the
  gate lives in the workflow itself and not merely in caller discipline.
- **MBP migration**: build → register `ufawkes-dojo-linux` → prove AC3 → then remove the macOS
  runner (`config.sh remove` + launchd bootout of `dev.ufawkes.dojo-runner`) so exactly one
  `self-hosted` runner exists and routing is deterministic.
- The trust gate (R4) is enforced in workflow expressions (above and in the Dojo recipe) **and**
  restated as a hard rule in the runbook.

### 4.7 Versioning & updates

- `FROM` digest bumped by Dependabot docker ecosystem (add to existing `dependabot.yml`).
- Runner/docker pins bumped by the same lock-bump discipline uFawkesAI uses (weekly cron creating
  `chore/image-lock-bump` PR, or Dependabot where applicable).
- Image releases ride Pipe's release-please (`v*` tags); consumers follow `sha256-` self-tags.

## 5. Acceptance criteria

Standing evidence rule: **no AC is met by assertion** — each requires the run URL or terminal
transcript, checked into the PR / attached to the plan's verification log. Green is claimed only
for runs that actually executed.

| # | Acceptance criterion | Evidence |
|---|---|---|
| **AC1** | `build-ci-image.yml` green on the branch: multi-arch build, all locked downloads hash-verified (`sha256sum -c` in build log), manifest print shows core's `tools.json` entries **plus** the layer's (R3), Trivy gate pass, cosign verify **and** attestation verify succeed against the published digest using the runbook's exact commands | workflow run URL + local command transcript |
| **AC2** | Mode 2 offline — **all four check classes**, not just pre-commit: with `--network none`, `pipe-ci pre-commit` (baseline) exits 0 on a Dojo checkout; after one online warm-up run, `pipe-ci pre-commit`, `pipe-ci pre-push`, `pipe-ci preflight`, and `pipe-ci security` each exit 0 offline from the cache volume | terminal transcript (each subcommand) |
| **AC3** | Mode 1 e2e on `ufawkes-dojo-linux`: Dojo dispatches for **markdown-lint**, **pre-flight** (test branch carrying the pre-commit wiring), and **pages** all GREEN on the new runner; `gh api …/actions/runners` shows it online and shows **no** macOS runner | run URLs + API output |
| **AC4** | Socket/live-testing: from inside the runner container, docker via the mounted colima socket works (`pipe-ci exec docker version` and one real stack flow, e.g. `verify-labs`-style `make up`, executed through it) | transcript |
| **AC5** | Hosted regression: push-path CI still green on `ubuntu-latest` after all changes | run URL |
| **AC6** | Pre-flight `runner` input PR: default (`ubuntu-latest`) run green **and** `self-hosted` dispatch green (positive half: R7 no-op + R4 dispatch path). **Negative half of the R4 gate, proven:** a non-dispatch event (PR/push) invoking the reusable with `runner: self-hosted` still executes on `ubuntu-latest` (event guard), and a grep of all suite workflows shows no `runs-on` path reaching `self-hosted` outside `workflow_dispatch` guards | run URLs + PR checks + guard-run output + grep result |
| **AC7** | Runbook: every command in it was executed verbatim during verification; failed commands are documented with their fix — no untested command ships (repo rule: nothing is described unless it has been run for real) | verification log |
| **AC8** | Piece 2b (step 0): diagnosis report for the red `build-devsecops-images` nightly (run 37275705085, `verify ai`) exists **before** this workflow is relied on for core digest updates; its fix is a separate change | report file/PR link |
| **AC9** | **Negative paths (R8) are executed, not asserted:** (i) `runner.sh` started without `RUNNER_TOKEN`/`RUNNER_REPO_URL` exits non-zero **naming the missing variable**; (ii) a `config.sh` failure (bogus URL) exits non-zero with the config log, never reaching `run.sh`; (iii) a deliberately planted failing check run through `pipe-ci` exits non-zero. Each transcript attached — proving "could not run" can never look green | three terminal transcripts |

## 6. Non-goals (v1)

- The git-host-outage tier (decided earlier: excluded).
- Migrating or replacing the uFawkesAI devsecops build (we consume its digest; ownership stays).
- Suite-wide switch of hosted jobs to `container:` (devsecops spec's own adoption track; we only
  keep the path open).
- Retiring GitHub-hosted as the default path (dispatch-only trust gate).
- The Obs `[self-hosted, synology]` deploy host (separate mechanism, untouched).
- arm64 runtime e2e (amd64-only verification this phase).

## 7. Sequencing

| Phase | Deliverable |
|---|---|
| **0** | Piece 2b — systematic-debugging diagnosis of the red devsecops nightly (AC8). Report first; fix separately. |
| **1** | This spec → owner review (this PR). Both pre-commit stages (default + `--hook-stage pre-push`) pass on it. |
| **2** | `plan.md` via the writing-plans skill → owner review. |
| **3** | Implement as small changes, **one PR per Pipe change**, batches < 400 lines: (a) image + lock + entrypoints, (b) publish workflow + Dependabot docker, (c) pre-flight `runner`-input + R4 event-guard PR (branch already pushed), (d) host unit (`runner/compose.yaml` + `.env.example`), (e) runbook. **Dojo-side changes are separate small changes per repo rule** (direct pushes to Dojo main): (f) MBP swap + macOS-runner retirement, (g) test-branch/probe-job cleanup. Both pre-commit stages pass on every PR. |
| **4** | Verify for real: AC1–AC9 green, verification log assembled. |
| **5** | Owner merges (Pipe is PR-only; agents never merge). |
| **6** | Rollout across the suite: each repo wires the dispatch input per the runbook; Obs/AI/Sec adoption follows. |

## 8. Resolved decisions (owner, 2026-10-06)

1. **Approach C** — new Pipe image `FROM` the published core digest (vs extending the devsecops
   lineage in uFawkesAI or migrating that build into Pipe).
2. **Both failure modes** (self-hosted runner path *and* fully local `pipe-ci`).
3. **GHCR, public, Pipe-owned** name: `ghcr.io/paruff/ufawkes-ci`.
4. **Base stays glibc/Debian-via-core; Alpine not reopened** — core's own measurements show tool
   mass dominates size (core ≈ 1.61 GB), and musl would break manylinux wheels, setup-python
   builds, and the runner's .NET runtime.
5. **Native macOS runners retired** (setup-python/sudo/gtar walls, with evidence).
6. Design approved in session (goals/non-goals, image, wiring, host unit, verification plan —
   this document's §1–§4; the AC list at §5 remains under review per the status line); spec
   location `docs/ci-runner-image/` approved.
7. **semgrep is baked in** (resolved during owner review of PR #146, 2026-10-06): engine
   hash-lock installed in the layer + a pinned, vendored ruleset so `pipe-ci security` stays
   offline-capable. Core's exclusion stands for the general image — the CI layer inverts its
   premise. Cost accepted: ≈ +245 MB (§10).

## 9. Open questions

None open — **OQ1 (semgrep) was resolved IN** during owner review of PR #146 (recorded as
decision 7 in §8).

## 10. Risks / remaining concerns

- **Publish-machinery duplication** (accepted cost of approach C): our workflow mirrors the
  devsecops one rather than sharing it. Mitigation: copy their structure, do not invent ours.
- **Image size ≈ 2.0 GB** (core 1.61 GB + ~245 MB semgrep engine + ~200 MB runner/docker layer):
  first pull on the MBP and colima disk usage; measured as part of AC1 and noted in the
  verification log.
- **Vendored semgrep ruleset staleness:** the ruleset only updates when the lock-bump discipline
  (§4.7) bumps it — new rule packs wait for that bump, the same trade-off core accepts for every
  locked tool.
- **Registration token lifecycle**: 1 h expiry, first-boot-only; state volume makes this a
  non-issue day-to-day, but a lost volume mid-incident needs the runbook's re-register flow
  (AC7 exercises it).
- **Core is at `2.0.0-rc.*`**: digest pinning makes this immaterial to determinism, but suite-wide
  rollout may want core's stable release first — owner call at phase 6.
- **Trivy gate noise**: reuse core's gate configuration/ignore posture so our gate and theirs
  fail on the same things (parity noted in plan).
