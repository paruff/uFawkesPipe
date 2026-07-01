# WP-005 — Add `upload-defectdojo` Telemetry Collector Step

**Type:** feat / security
**Depends on:** WP-002 (fawkes-net), WP-004 (Trivy steps)
**Branch:** `feature/wp-005-defectdojo-upload`

---

## 1. Problem

Security findings from Gitleaks (secrets-scan) and Trivy (vuln-scan-fs, vuln-scan-image) currently write JSON artifacts to `artifacts/security/` but have no downstream consumer. The findings go nowhere — they are not aggregated, tracked, or actionable.

This step collects the three JSON artifact files and POSTs them to DefectDojo's `/api/v2/import-scan/` endpoint so security teams can track, triage, and remediate vulnerabilities in a centralized platform.

---

## 2. Requirements

### Functional

| # | Requirement | Rationale |
|---|---|---|
| F1 | Step named `upload-defectdojo` uses image `curlimages/curl:8.6.0` | Pinned, minimal image for HTTP calls |
| F2 | Secret `defectdojo_api_token` injected via `from_secret` | Never hardcode credentials |
| F3 | Step only runs on `branch: main` | Only aggregate findings on main branch merges |
| F4 | Shell loop iterates over `gitleaks.json`, `trivy-repo.json`, `trivy-image.json` | Three scanner outputs from previous steps |
| F5 | Each file checked for existence with `[ -f "$path" ] \|\| continue` before POSTing | Defensive — scan may be skipped in some runs |
| F6 | `scan_type` correctly mapped: `gitleaks` → `Gitleaks Scan`, `trivy-repo`/`trivy-image` → `Trivy Scan` | DefectDojo requires specific scan type identifiers |
| F7 | `product_name` uses `${CI_REPO_NAME}` Woodpecker variable | Auto-create/link product by repo name |
| F8 | `engagement_name` is static `CI-Engagement` | Single engagement per product for CI runs |
| F9 | Failed uploads print `WARN:` prefix and do not exit non-zero | Non-blocking — pipeline continues on upload failure |

### Non-Functional

| # | Requirement | Rationale |
|---|---|---|
| NF1 | Structured JSON logging (DORA format) for observability | Consistent with all other pipeline steps |
| NF2 | No secrets in logs — token passed via env var | Security hygiene |
| NF3 | Works with DefectDojo on `fawkes-net` at `http://defectdojo:8080` | Network prerequisite from WP-002 |

---

## 3. Acceptance Criteria

1. Step `upload-defectdojo` exists in `.woodpecker.yml` with image `curlimages/curl:8.6.0`
2. Step has `environment.DOJO_API_TOKEN.from_secret: defectdojo_api_token`
3. Step has `when: branch: main`
4. Commands contain shell loop over `gitleaks trivy-repo trivy-image`
5. Loop checks `[ -f "$path" ] || continue` before each POST
6. `scan_type` mapping implemented via `case` statement
7. `product_name` uses `${CI_REPO_NAME}`
8. Failed uploads output `WARN:` and do not fail step
9. `.env.example` documents `DOJO_API_TOKEN` placeholder with comment
10. `tests/unit/test_woodpecker_yml.py` updated with `TestUploadDefectDojoStep` class
11. `pytest tests/` passes with zero failures

---

## 4. Dependencies

- **WP-002**: `fawkes-net` external network for DefectDojo DNS resolution
- **WP-004**: `vuln-scan-fs` and `vuln-scan-image` steps producing Trivy JSON artifacts

---

## 5. Out of Scope

- DefectDojo provisioning (assumed pre-existing on `fawkes-net`)
- Vault/Infisical integration (Woodpecker native secrets used)
- Product/engagement auto-creation verification (depends on DefectDojo version — human verification required)

---

## 6. Open Questions (Block Implementation if Unresolved)

| # | Question | Owner | Target |
|---|---|---|---|
| Q1 | Does DefectDojo `/api/v2/import-scan/` accept `product_name` for auto-creation, or is `product_id` required? | Platform engineer | Before implementation |
