# Plan: DAST step writes reports where later steps read them (#289)

The generated `dast` step ran ZAP without `/zap/wrk` and wrote reports outside the workspace. `scripts/generate_woodpecker_yml.py` now emits `dast-prep` (`busybox:1.36.1`, root, makes `artifacts/security` writable) and `dast` (ZAP as its non-root user, `/zap/wrk` symlinked to the reports dir, relative `-r/-x` paths). `dast.openapi_url` is a new optional field; without it only the baseline scan runs. A pipeline that relied on the default API scan must set `openapi_url` (migration note in `docs/pipeline-contract.md`).

## Verification Strategy

| Criterion | Evidence |
|---|---|
| Reports land in `artifacts/security`, no `user: root` on the ZAP step | `test_dast_reports_reach_workspace_and_api_scan_is_optional`; local Docker run of `zaproxy/zap-stable` as user `zap` wrote `zap-baseline.xml` into the mounted workspace |
| `openapi_url` optional | same test (no `zap-api-scan.py` without it); `test_dast_enabled_adds_zap_commands` (present with it) |
| No `source` in the step | same test asserts `"source "` is absent |
| Lab baseline run green and picked up by `defectdojo-upload` | Not yet run: paruff/uFawkesDojo#139 lab-01, to be re-run against a release containing this change |
