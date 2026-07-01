# WP-004 — Add `vuln-scan-fs` and `vuln-scan-image` Trivy steps

**Type:** feat / security
**Depends on:** WP-001 (init), WP-003 (secrets-scan)
**Branch:** `feature/wp-004-trivy-vuln-scan`

---

## 1. Problem

The current `.woodpecker.yml` has a single `security-scan` step that runs `trivy fs --exit-code 1 --severity HIGH,CRITICAL` on `branch: main` only. This does not match the v0.2 pipeline design:

- Filesystem scanning should run on **every push** (not just main) so developers get CVE feedback early
- Image scanning should run **after build** on `main` only
- Both scans must write JSON artifacts to `artifacts/security/` for downstream DefectDojo ingestion
- The current step fails the pipeline on HIGH/CRITICAL findings, but the v0.2 design says findings go to DefectDojo (exit-code 0, no hard gate at v0.2)

---

## 2. Requirements

### Functional

| # | Requirement | Rationale |
|---|---|---|
| F1 | Step named `vuln-scan-fs` uses image `aquasec/trivy:latest` | Trivy scanner for filesystem CVE scan |
| F2 | `vuln-scan-fs` command: `trivy fs --format json --output artifacts/security/trivy-repo.json --no-progress .` | JSON output for DefectDojo; `--no-progress` for clean CI logs |
| F3 | `vuln-scan-fs` runs on every push (no `when:` branch restriction) | Developers get CVE feedback on all branches |
| F4 | `vuln-scan-fs` exits with code 0 (findings reported, not fatal) | Findings go to DefectDojo, not a pipeline gate at v0.2 |
| F5 | Comment above `vuln-scan-fs` explains the `latest` tag exception for scanner images | Documented exception to pinned-image policy |
| F6 | Step named `vuln-scan-image` uses image `aquasec/trivy:latest` | Trivy scanner for built image CVE scan |
| F7 | `vuln-scan-image` command: `trivy image --format json --output artifacts/security/trivy-image.json --no-progress <image-ref>` | JSON output for DefectDojo |
| F8 | `vuln-scan-image` has `when: branch: main` condition | Image scan requires a built image, which only exists on main |
| F9 | Image ref uses Woodpecker built-in variables for registry, repo, and short SHA | Consistent with build step image tagging |
| F10 | Old `security-scan` step removed | Replaced by the two new steps |

### Non-Functional

| # | Requirement | Rationale |
|---|---|---|
| NF1 | Structured JSON logging (DORA format) in both steps | Consistent with all other pipeline steps |
| NF2 | `--no-progress` flag on both scans | Reduces CI log noise |
| NF3 | No secrets required for Trivy steps | Trivy pulls public CVE DB, no auth needed |

---

## 3. Acceptance Criteria

1. Step `vuln-scan-fs` exists in `.woodpecker.yml` with image `aquasec/trivy:latest`
2. `vuln-scan-fs` command includes `--format json --output artifacts/security/trivy-repo.json --no-progress .`
3. `vuln-scan-fs` has **no** `when:` branch restriction (runs on every push)
4. Step `vuln-scan-image` exists in `.woodpecker.yml` with image `aquasec/trivy:latest`
5. `vuln-scan-image` command includes `--format json --output artifacts/security/trivy-image.json --no-progress`
6. `vuln-scan-image` has `when:` condition `branch: main`
7. Comment explaining `latest` tag exception exists above or inline with both Trivy steps
8. Old `security-scan` step **removed** from `.woodpecker.yml`
9. `tests/unit/test_woodpecker_yml.py` updated with `TestVulnScanFsStep` and `TestVulnScanImageStep` classes
10. `pytest tests/` passes with zero failures

---

## 4. Dependencies

- **WP-001** (init): artifact directories must exist before scan writes output
- **WP-003** (secrets-scan): must run before filesystem scan (secret leaks are more critical than CVEs)

---

## 5. Out of Scope

- Hard gate on CRITICAL severity in image scan (v0.3 item — requires DefectDojo policy round-trip)
- `upload-defectdojo` step (WP-005)
- `build` step (WP-009) — `vuln-scan-image` references the build output but does not include the build step itself
- SBOM generation (future)
