# Plan: generated sast step runs as generated (#287)

The generated `sast` step failed three ways in a real Woodpecker 3.20.1 run:
a hardcoded `/drone/src` workspace path, no credentials, and a quality-gate
poll on a nonexistent endpoint with no bound. The work is tracked in
[#287](https://github.com/paruff/uFawkesPipe/issues/287).

## Verification Strategy

- Unit tests in `tests/unit/test_pipeline_generator.py`
  (`TestSastStepRunsAsGenerated`) cover each defect: no `/drone/src`, optional
  helper script, `from_secret` environment, `project_status` endpoint, and a
  bounded loop. Two tests run the real gate loop against a stub `curl`
  (timeout on `PENDING`; `NONE` then `OK`).
- End to end: a fresh app repo holding only `.fawkespipe.yml` and the generated
  `.woodpecker.yml`, run with `woodpecker-cli v3.20.1 exec --local
  --pipeline-event push` against a real `sonarqube:lts-community` container.
  The scanner authenticates and the gate reaches `OK`.
- `make precommit` passes, and the checked-in example under
  `examples/fawkespipe-contract-migration/` matches the generator output.
