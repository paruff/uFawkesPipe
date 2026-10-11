# ufawkes-ci verification log

Evidence for `spec.md` §5, recorded as the plan's tasks run. Green is claimed only
for runs that executed; a row with no evidence below is not yet verified.

Image under test: built locally from `images/ci` (`linux/amd64`, Colima, Docker 29.5.2).
Base: `fawkes-core` 2.0.0, `sha256:15a466e0…c29bd`.

## PR A: image, lock, entrypoints

| Check | Command | Result |
|---|---|---|
| R3 hash mismatch fails the build | build with one `runner.lock` hash corrupted | `runner.tgz: FAILED`, `sha256sum: WARNING: 1 computed checksum did NOT match`, build exit 1 |
| R3 real lock builds | build with the committed lock | four artifacts `OK`, build exit 0 |
| R3 manifest superset | compare `.[].name` of `/etc/ufawkes/tools.json` against the base image | core 15 names, all kept; image 20; added `actions-runner docker-cli docker-compose semgrep semgrep-rules` |
| AC2 semgrep offline | `docker run --network none … semgrep scan --config /opt/ufawkes/semgrep-rules --error` on a planted `${{ github.event.issue.title }}` workflow, and on a clean one | planted: exit 1 (finding); clean: exit 0 |
| AC9-i missing env | `runner.sh` without `RUNNER_TOKEN` | exit 2, stderr `runner.sh: missing required env: RUNNER_TOKEN` |
| AC9-ii failed registration | `runner.sh` with `RUNNER_REPO_URL=https://invalid.example.invalid` | exit 3, config log printed (`Name or service not known`), `run.sh` not reached |
| AC9-iii secret found | `pipe-ci security` (`--network none`) in a repo with a committed private key | exit 1, `leaks found: 1` |
| AC2 `pipe-ci security`, clean | same, repo with only a README | exit 0 (gitleaks, trivy fs, semgrep all offline) |
| AC2 `pipe-ci pre-commit --baseline`, clean | `--network none`, small clean repo | exit 0, 12 hooks passed |
| Socket | `-v /var/run/docker.sock:… pipe-ci exec docker version` | `client=29.9.0 server=29.5.2` |

## Not verified yet

- **AC8** (diagnosis of the red `build-devsecops-images` nightly, Task 0): not done. It gates
  merging a Dependabot core-digest bump, not this build.
- **Multi-arch, signing, SBOM, provenance** (Task 6 publish workflow): not built yet. Only
  `linux/amd64` was built, and only locally.
- **arm64** build of `images/ci`: not run.
- **PR CI run URL:** added when the PR's checks have run.

## Findings and rulings made while building

1. **Plan digest typo.** The plan's base digest has 65 hex characters. Used the published
   `fawkes-core` **2.0.0** digest instead (Pipe#166: build on the current 2.0.0 core until
   the AI-DLC release, then bump).
2. **docker-cli has no published checksum.** Pinned by hash from a first download over HTTPS
   (trust on first use). Compose and the runner were cross-checked against their publishers'
   checksums.
3. **`tools.json` is an array** of `{name, version, sha256, variant}`, not `{tools: …}`. Entries
   are appended in that shape. The plan's list of core keys (with `opencode`, `superpowers`)
   matches rc.3, not 2.0.0; the superset test compares against the base image itself.
4. **`p/ci` cannot be rebuilt from the semgrep-rules repo.** The vendored set is the CI-themed
   directories (`generic/ci`, `yaml/github-actions`, `dockerfile`, `bash`), a close
   approximation, not the registry's pack.
5. **semgrep 1.179.0**, the version Pipe's pre-push hook pins, not the latest.
6. Manifest entries are appended in the task that installs each tool.
7. **`semgrep --validate` needs the network** (it fetches `p/semgrep-rule-lints`), so it cannot
   prove offline completeness. A real scan under `--network none` is the test.
8. **The runner tarball keeps `config.sh` and `run.sh` at its root**, not under `bin/`. Unpacked
   to `/opt/ufawkes-runner`, so `.runner` and `_work` land where the spec wants them.
9. `preflight`, `lint` and `unit` were underspecified; defined in `pipe-ci`'s header.
10. **Trivy needs its vulnerability DB**, so `pipe-ci security` failed offline. The DB is baked
    in at build time and used with `--skip-db-update`. It is as old as the image.
11. **Offline pre-commit is the baseline config.** A repo's own config with remote hooks cannot
    install them with no network (fails loudly, exit 3). `pipe-ci pre-commit --baseline` runs
    core's `language: system` baseline.
12. **One vendored rule does not parse under 1.179.0** (`yaml/github-actions/security/curl-eval`);
    with `--error` it makes every scan exit 2. Excluded, with a build-time scan of a clean file
    as a guard.

## Dojo, as a target for the baseline

`pipe-ci pre-commit --baseline` on a Dojo checkout runs all 16 hooks offline and exits 1 on two
real findings, not an image fault: `shellcheck` info-level notes in
`brown-belt/module-16-incident-management/lab-01/validate.sh`, and `detect-secrets` flagging a hex
string at `modules/brown-belt/module-14-dora-deep-dive.md:210`. The plan's AC2 rehearsal expected
exit 0 there; that needs those two fixed or allow-listed in Dojo.
