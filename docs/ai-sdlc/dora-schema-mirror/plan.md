# Plan: check the DORA schema mirror against uFawkesObs

**Traces to:** uFawkesPipe#218, paruff/uFawkes.dev#230 | **Status:** In review

`contracts/dora-events/*.schema.json` mirrors uFawkesObs's `dora/events/`. Nothing
kept them in step, so a field added in uFawkesObs broke `notify-obs` silently.

| Step | What                                                                                              |
| ---- | ------------------------------------------------------------------------------------------------- |
| S1   | `contracts/dora-events/OBS_RELEASE` pins the uFawkesObs release the mirror matches                 |
| S2   | A unit test reads Obs's schemas at that release and compares event types, required fields, properties |
| S3   | `docs/dora-contract.md` replaces its "Known gap" section with how the sync works                   |

## Verification Strategy

| Check                                            | How                                                                                       |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| The mirror matches Obs at the pinned release     | `pytest tests/unit/test_dora_schema_mirror.py`: 5 cases pass against v1.0.1               |
| A removed required field is caught               | Delete a field from `pr-event.schema.json`: the matching case fails                       |
| CI runs it                                       | `ci-tests.yml` runs `pytest tests/unit/`; a network error fails there and skips offline   |
| Not covered yet                                  | A new uFawkesObs release: moving `OBS_RELEASE` is a manual step in the same PR as the port |
