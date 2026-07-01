# WP-005 — Design: Add `upload-defectdojo` Telemetry Collector Step

**Depends on:** specification.md (WP-005), WP-002 (fawkes-net), WP-004 (Trivy steps)

---

## 1. Impacted Components

| Component | File | Change |
|---|---|---|
| Pipeline definition | `.woodpecker.yml` | Add `upload-defectdojo` step after `vuln-scan-image` |
| Pipeline tests | `tests/unit/test_woodpecker_yml.py` | Add `TestUploadDefectDojoStep` class |
| Example env | `.env.example` | Add `DOJO_API_TOKEN` placeholder |

No other files modified.

---

## 2. Step Design

### 2.1 Position in Pipeline

The `upload-defectdojo` step runs **after** `vuln-scan-image` and **before** `notify-obs`. This ensures all three scanner artifacts (gitleaks.json, trivy-repo.json, trivy-image.json) are available before the upload attempt.

```
init → secrets-scan → lint-yaml → lint-shell → validate-pipeline-contract
  → vuln-scan-fs → vuln-scan-image → upload-defectdojo → notify-obs
```

### 2.2 Step Definition

```yaml
  - name: upload-defectdojo
    image: curlimages/curl:8.6.0
    environment:
      DOJO_API_TOKEN:
        from_secret: defectdojo_api_token
    commands:
      - |
        echo '{"@timestamp":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","level":"info","logger":"security","message":"Starting DefectDojo upload","pipeline":"'"${CI_PIPELINE_NUMBER:-unknown}"'","repo":"'"${CI_REPO:-unknown}"'","step":"upload-defectdojo"}'
      - |
        for f in gitleaks trivy-repo trivy-image; do
          path="artifacts/security/${f}.json"
          if [ ! -f "$path" ]; then
            echo '{"@timestamp":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","level":"warn","logger":"security","message":"Artifact not found, skipping","file":"'"$path"'","step":"upload-defectdojo"}'
            continue
          fi
          case "$f" in
            gitleaks)   scan_type="Gitleaks Scan" ;;
            trivy-repo|trivy-image) scan_type="Trivy Scan" ;;
          esac
          HTTP_CODE=$(curl -sf -X POST "http://defectdojo:8080/api/v2/import-scan/" \
            -H "Authorization: Token $DOJO_API_TOKEN" \
            -F "active=true" -F "verified=false" \
            -F "scan_type=${scan_type}" \
            -F "engagement_name=CI-Engagement" \
            -F "product_name=${CI_REPO_NAME}" \
            -F "file=@${path}" \
            -w '%{http_code}' -o /dev/null 2>&1) && rc=$? || rc=$?
          if [ $rc -eq 0 ] && [ "$HTTP_CODE" = "201" ]; then
            echo '{"@timestamp":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","level":"info","logger":"security","message":"DefectDojo upload successful","file":"'"${f}"'","http_code":"'"${HTTP_CODE}"'","step":"upload-defectdojo"}'
          else
            echo '{"@timestamp":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","level":"warn","logger":"security","message":"DefectDojo upload failed","file":"'"${f}"'","http_code":"'"${HTTP_CODE:-000}"'","step":"upload-defectdojo"}'
          fi
        done
    when:
      - event: push
        branch: main
```

### 2.3 Key Design Decisions

**Non-blocking upload:** Each upload failure prints a warning but does not exit non-zero. This ensures the pipeline completes even if DefectDojo is unreachable.

**HTTP code capture:** Using `-w '%{http_code}' -o /dev/null` to capture the HTTP status code for observability logging. DefectDojo returns 201 on successful import.

**DORA logging:** Each operation (file found, upload success, upload failure) emits a structured JSON log entry for uFawkesObs ingestion.

**Defensive file check:** Each artifact file is checked for existence before POSTing. If the `build` step (WP-009) is not yet implemented, `trivy-image.json` won't exist — the loop skips it gracefully.

---

## 3. Test Design

### 3.1 `TestUploadDefectDojoStep` class

| Test | Assertion |
|---|---|
| `test_step_exists` | Step named `upload-defectdojo` exists in steps list |
| `test_uses_curl_image` | Image is `curlimages/curl:8.6.0` |
| `test_has_dojo_api_token_secret` | Step has `environment.DOJO_API_TOKEN.from_secret: defectdojo_api_token` |
| `test_branch_main_only` | Step has `when:` with `branch: main` condition |
| `test_loops_over_gitleaks` | Commands reference `gitleaks` in loop |
| `test_loops_over_trivy_repo` | Commands reference `trivy-repo` in loop |
| `test_loops_over_trivy_image` | Commands reference `trivy-image` in loop |
| `test_checks_file_existence` | Commands include `[ -f "$path" ]` or `[ ! -f "$path" ]` |
| `test_scan_type_gitleaks` | Commands map `gitleaks` to `Gitleaks Scan` |
| `test_scan_type_trivy_repo` | Commands map `trivy-repo` to `Trivy Scan` |
| `test_scan_type_trivy_image` | Commands map `trivy-image` to `Trivy Scan` |
| `test_uses_product_name` | Commands reference `CI_REPO_NAME` |
| `test_uses_engagement_name` | Commands reference `CI-Engagement` |
| `test_non_blocking_warn` | Commands do NOT use `exit` on failure; uses `WARN:` or logging pattern |
| `test_has_dora_logging` | Commands include DORA JSON structured logging with `@timestamp` |

---

## 4. `.env.example` Change

Add after existing secret placeholders:

```
# DefectDojo API token for security scan ingestion
DOJO_API_TOKEN=your-defectdojo-api-token
```

---

## 5. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| DefectDojo not running on `fawkes-net` | Medium | Non-blocking (warns only); step does not fail pipeline |
| `product_name` field not accepted by DefectDojo API version | Medium | Human verification required before implementation (noted in spec as Q1) |
| Large scan artifacts causing slow uploads | Low | Trivy/Gitleaks JSON artifacts are typically < 1 MB |

---

## 6. File Change Summary

| File | Action | Notes |
|---|---|---|
| `.woodpecker.yml` | Modify | Add `upload-defectdojo` step after `vuln-scan-image` |
| `.env.example` | Modify | Add `DOJO_API_TOKEN` placeholder |
| `tests/unit/test_woodpecker_yml.py` | Modify | Add `TestUploadDefectDojoStep` class |
