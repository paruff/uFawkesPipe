# Plan: run Trivy and Bandit in images that contain them (#288)

The generated `sast` step ran `trivy fs` and `bandit` inside `sonarsource/sonar-scanner-cli`, which has neither. `scripts/generate_woodpecker_yml.py` now emits `sast` (Sonar only), `sast-trivy` (`aquasec/trivy:0.74.0`) and `sast-bandit` (`python:3.12-slim`, `pip install bandit`). The `.fawkespipe.yml` contract is unchanged.

## Verification Strategy

| Criterion | Evidence |
|---|---|
| Trivy and Bandit in their own steps with images that contain them | `tests/unit/test_pipeline_generator.py`: `TestTrivyInSast`, `TestBanditInSast` check each step's image and commands, and that `sast` has neither tool |
| `bandit.json` still written, then gated | `test_bandit_step_image_has_bandit_and_writes_report`; the existing flag-validity test runs real bandit when it is on PATH |
| Options work with defaults, with a step-list test | Default-contract tests above; `sast.trivy.enabled: false` and `sast.bandit.enabled: false` omit the steps |
| Lab no longer disables them | paruff/uFawkesDojo#144, to be re-run against a release containing this change |
