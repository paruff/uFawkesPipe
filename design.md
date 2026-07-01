# WP-004 — Design: Add `vuln-scan-fs` and `vuln-scan-image` Trivy steps

**Depends on:** specification.md (WP-004)

---

## 1. Impacted Components

| Component | File | Change |
|---|---|---|
| Pipeline definition | `.woodpecker.yml` | Remove `security-scan` step; add `vuln-scan-fs` and `vuln-scan-image` steps |
| Pipeline tests | `tests/unit/test_woodpecker_yml.py` | Add `TestVulnScanFsStep` and `TestVulnScanImageStep` test classes |

No other files are modified. No compose.yaml changes, no contract changes, no new scripts.

---

## 2. `.woodpecker.yml` Step Design

### 2.1 `vuln-scan-fs` (replaces `security-scan`)

**Position:** After `validate-pipeline-contract` step (current step index 5). This is the natural position — the filesystem scan runs on the source code, which is available after checkout and lint/test validation.

**Why not a hard gate?** The v0.2 design (design.md §2.2) explicitly states: "`--exit-code 0` — findings go to DefectDojo, not pipeline gate. Hard gate on image scan for CRITICAL severity is a v0.3 item." Therefore, `vuln-scan-fs` must NOT use `--exit-code 1`.

**Step definition:**

```yaml
  # aquasec/trivy:latest is intentionally unpinned — scanner images need
  # current CVE databases. This is a documented exception to pinned-image policy.
  - name: vuln-scan-fs
    image: aquasec/trivy:latest
    commands:
      - echo '{"@timestamp":"...","level":"info","logger":"security","message":"Running Trivy filesystem scan",...,"step":"vuln-scan-fs"}'
      - trivy fs --format json --output artifacts/security/trivy-repo.json --no-progress . && rc=$? || rc=$?
      - echo '{"@timestamp":"...","level":"...","logger":"security","message":"Trivy filesystem scan completed","exit_code":'${rc}',...,"step":"vuln-scan-fs"}'
      - exit $rc
```

**Key differences from current `security-scan`:**
- Removed `--exit-code 1 --severity HIGH,CRITICAL` → no gate, exit-code 0 on findings
- Added `--format json --output artifacts/security/trivy-repo.json` → JSON artifact for DefectDojo
- Removed `when: branch: main` → runs on every push
- Added DORA structured logging

### 2.2 `vuln-scan-image` (new, runs after build)

**Position:** After `notify-obs` (or after a future `build` step). Since the `build` step does not yet exist in the current `.woodpecker.yml`, this step will be placed after `notify-obs` with a conditional `when: branch: main`. The image reference uses Woodpecker variables that the `build` step (WP-009) will set.

For now, the image reference will use the same pattern as the design.md §5 target: `${REGISTRY_USERNAME}/${CI_REPO_NAME}:${CI_COMMIT_SHA:0:7}`. This requires the `REGISTRY_USERNAME` secret (from_secret). Since the build step does not exist yet, the `vuln-scan-image` step will fail if it actually tries to scan a non-existent image. This is acceptable because:
1. The `when: branch: main` condition limits it to main branch
2. The build step (WP-009) will be added later and will produce the image

**Wait — better approach:** Since the build step doesn't exist yet, and `vuln-scan-image` requires a built image, I should add the step definition now but understand it will only become functional when the build step is added (WP-009). The step will sit in the pipeline definition, correctly configured, and will be a no-op (or fail gracefully) until the build step provides the image. The `when:` condition already limits it to `main` only.

**Step definition:**

```yaml
  # aquasec/trivy:latest is intentionally unpinned — scanner images need
  # current CVE databases. This is a documented exception to pinned-image policy.
  - name: vuln-scan-image
    image: aquasec/trivy:latest
    environment:
      REGISTRY_USERNAME:
        from_secret: registry_username
    commands:
      - echo '{"@timestamp":"...","level":"info","logger":"security","message":"Running Trivy image scan",...,"step":"vuln-scan-image"}'
      - trivy image --format json --output artifacts/security/trivy-image.json --no-progress ${REGISTRY_USERNAME}/${CI_REPO_NAME}:${CI_COMMIT_SHA:0:7} && rc=$? || rc=$?
      - echo '{"@timestamp":"...","level":"...","logger":"security","message":"Trivy image scan completed","exit_code":'${rc}',...,"step":"vuln-scan-image"}'
      - exit $rc
    when:
      - event: push
        branch: main
```

---

## 3. Test Design

### 3.1 `TestVulnScanFsStep`

| Test | Assertion |
|---|---|
| `test_step_exists` | Step named `vuln-scan-fs` exists in steps list |
| `test_uses_trivy_latest` | Image is `aquasec/trivy:latest` |
| `test_has_json_format_output` | Commands include `--format json` |
| `test_output_path` | Commands include `--output artifacts/security/trivy-repo.json` |
| `test_has_no_progress` | Commands include `--no-progress` |
| `test_scans_current_dir` | Commands include `.` as scan target |
| `test_no_branch_restriction` | Step has NO `when:` condition (runs on all pushes) |
| `test_no_hard_gate_exit_code` | Commands do NOT include `--exit-code 1` |
| `test_has_dora_logging` | Commands include DORA JSON structured logging |

### 3.2 `TestVulnScanImageStep`

| Test | Assertion |
|---|---|
| `test_step_exists` | Step named `vuln-scan-image` exists in steps list |
| `test_uses_trivy_latest` | Image is `aquasec/trivy:latest` |
| `test_has_json_format_output` | Commands include `--format json` |
| `test_output_path` | Commands include `--output artifacts/security/trivy-image.json` |
| `test_has_no_progress` | Commands include `--no-progress` |
| `test_branch_main_only` | Step has `when:` with `branch: main` condition |
| `test_uses_registry_username_secret` | Step has `environment.REGISTRY_USERNAME.from_secret: registry_username` |
| `test_image_ref_uses_ci_variables` | Commands reference `CI_REPO_NAME` and `CI_COMMIT_SHA` |
| `test_has_dora_logging` | Commands include DORA JSON structured logging |

### 3.3 Update existing tests

Remove/update any tests that reference the old `security-scan` step by name.

---

## 4. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| `vuln-scan-image` runs but no image exists (build step missing) | High (now) | Step has `when: branch: main`; not triggered on PRs. Will be addressed when build step is added in WP-009. |
| Trivy `latest` tag introduces breaking changes | Low | Trivy CLI has been stable; `--format json --output --no-progress` flags are well-established |
| `bash substring ${CI_COMMIT_SHA:0:7}` not universally supported | Medium | Woodpecker step containers use `dash` or `bash` — verify; if not supported, use `cut -c1-7` instead |

---

## 5. File Change Summary

| File | Action | Notes |
|---|---|---|
| `.woodpecker.yml` | Modify | Remove `security-scan`, add `vuln-scan-fs` and `vuln-scan-image` |
| `tests/unit/test_woodpecker_yml.py` | Modify | Add `TestVulnScanFsStep` and `TestVulnScanImageStep` classes |
