# Design — CONSOLIDATE-SEC

## 1. Constraint Check

The only architectural judgment call is *how* to bring in uFawkesSec's
history: `git subtree add` vs a flat `cp -r` + separate commit. Subtree
preserves per-file blame/history; a flat copy loses it. Subtree costs one
extra remote add + one command; the repo is small (45 files) so the cost is
negligible. **Decision: git subtree.**

Second call: final directory shape. Landing everything under a permanent
`security/` wrapper would turn this into "two products in one repo"
(exactly what merging is meant to avoid). Flattening into uFawkesPipe's
existing `config/`, `policy/`, `docs/`, `tests/unit/` follows the "many
small files, organize by feature" convention already used in this repo, and
there are no filename collisions (checked: no `config/` dir exists yet in
uFawkesPipe; `tests/unit/conftest.py` exists but uFawkesSec's
`tests/unit/conftest.py` only provides compose/workflow fixtures, checked
for symbol overlap before merging). **Decision: subtree lands at
`security/` as a staging point, then a second commit moves each subdir to
its flat final home and deletes the empty wrapper.**

## 2. Evidence Gathered

| Question | Evidence | Answer |
| --- | --- | --- |
| Port collisions? | Pipe: 8000/9000/9443. Sec: 8080/8082/4954(internal) | None |
| Volume/service-name collisions? | Pipe: woodpecker-agent/server, sonarqube, portainer. Sec: defectdojo(+nginx/celery-beat/celery-worker), infisical, trivy-server, falco | None |
| Agent-definition collisions? | uFawkesSec's `.agents/` has only `logs/`, no `agents/*.md` | None |
| Is `policy-check` already wired in `.woodpecker.yml`? | `grep -n "conftest\|rego\|policy"` on `.woodpecker.yml` returns nothing | No — CHANGELOG #49 entry is stale; step never shipped |
| `.gitleaks.toml` diff | `diff` — zero output | Identical, no reconciliation needed |
| `.pre-commit-config.yaml` diff | uFawkesSec uses older hook revs + `detect-secrets`/`.secrets.baseline` instead of gitleaks; uFawkesPipe consolidated on gitleaks only (see its own comment: "GitGuardian and detect-secrets removed as redundant") | Adopt uFawkesPipe's version; drop uFawkesSec's `detect-secrets` hook + `.secrets.baseline` |
| LICENSE | uFawkesPipe: real Apache-2.0 file. uFawkesSec: README says MIT, no LICENSE file exists | Keep Apache-2.0 (the one that's real); fix README claim |
| `compose.yaml` naming convention mismatch | uFawkesPipe: `compose.yaml`=standalone, `compose.suite.yaml`=suite (needs uFawkesRes). uFawkesSec: inverted — `compose.yaml`=suite (needs uFawkesRes), `compose-standalone.yaml`=standalone | Adopt uFawkesPipe's convention: merge Sec's suite-mode services into `compose.suite.yaml`, standalone-mode services (with embedded postgres/valkey) into a new `compose.yaml` addition |
| Docker available this session? | `docker ps` → `dial unix .../docker.sock: connect: no such file or directory` | No — live-system boot deferred to human, documented explicitly (not silently skipped) |
| `test_policy.py` dependency | `subprocess.run(["docker", "run", ...])` calling `openpolicyagent/conftest` | Requires Docker — moved in as-is, not executed this session |
| `test_compose_yaml.py` / `test_workflow_validation.py` dependency | Pure `pyyaml` + `pytest`, no `docker`/`conftest`/`opa` calls | Runnable this session |

## 3. Compose Merge Approach

`fawkes-net` currently exists as an **external** network in both repos'
suite-mode compose files (created out-of-band via `make network` so two
independently-deployed repos could find each other). Once merged, both
sides of that network live in one repo — `fawkes-net` becomes an ordinary
internal Compose network in `compose.suite.yaml`, and `make network` /
the external-network assumption is removed. `test_compose_yaml.py`'s
assertion that `fawkes-net` is external gets updated to match.

`.woodpecker.yml`'s `upload-defectdojo` step already assumes
`http://defectdojo:8080` is reachable from the same Docker network the
Woodpecker agent joins — true before (via external `fawkes-net`) and true
after (via internal network), so that step's command text does not change,
only the compose file that defines the network.

## 4. `policy-check` Step Design

New step in `.woodpecker.yml`, inserted after `secrets-scan`/`vuln-scan-*`
and before `build-image` (security stage), mirroring uFawkesSec's own
pipeline snippet but pointed at the local path instead of a runtime
`git clone`:

```yaml
- name: policy-check
  image: openpolicyagent/conftest:v0.57.0
  depends_on: [vuln-scan-fs]
  commands:
    - conftest test --policy policy/ compose.yaml compose.suite.yaml .woodpecker.yml
```

This is a hard gate (non-zero exit fails the step) — consistent with
`secrets-scan`'s hard-gate precedent, since policy-as-code violations are
the same class of blocking finding as a leaked secret.

## 5. Impacted Components

| Component | Change |
| --- | --- |
| `compose.yaml` | + defectdojo/infisical/trivy-server/falco standalone-mode services (embedded postgres/valkey) |
| `compose.suite.yaml` | + same services in suite-mode form (uses uFawkesRes postgres/valkey); `fawkes-net` becomes internal |
| `policy/*.rego` | New: 5 files moved from uFawkesSec unchanged |
| `config/{defectdojo,infisical,falco}/*` | New: moved from uFawkesSec unchanged |
| `.woodpecker.yml` | + `policy-check` step |
| `tests/unit/test_compose_yaml.py` | Moved + updated: `fawkes-net` external→internal assertion |
| `tests/unit/test_workflow_validation.py` | Moved unchanged |
| `tests/unit/test_policy.py` | Moved unchanged, not executed this session (Docker-dependent) |
| `AGENTS.md` | Merge uFawkesSec's security-plane conventions section in |
| `README.md` | Ecosystem table: uFawkesSec row → "merged" note instead of external link; correct LICENSE badge if any |
| `docs/policy-guide.md`, `docs/quickstart.md` (from Sec) | Moved into `docs/` |
| `.pre-commit-config.yaml` | No change (already the version being kept) |
| uFawkesSec's `.secrets.baseline`, `.pipeline.yml` | Not carried over — superseded by uFawkesPipe's gitleaks/`.woodpecker.yml` equivalents |
