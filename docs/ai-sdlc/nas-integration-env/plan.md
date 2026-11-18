# Plan: the NAS as the test and integration environment

**Traces to:** [`../v2.0.0/spec.md`](../v2.0.0/spec.md) (AC-PIPE-01, AC-DORA-01).
Proposal, not yet accepted: nothing here is built.

## Intent

The MacBook Pro is the dev environment. The Synology NAS is the test and
integration environment: uFawkesPipe (Woodpecker) and uFawkesObs run there
together, so a real pipeline run can post to a real uFawkesObs. The three
elements are GitHub, uFawkesPipe and uFawkesObs. v2.0.0 needs that run and
doesn't have it: `notify-obs` and `build-image` have only been verified by
unit tests and a local stub.

## Decisions to take

| Question | Recommendation | Why |
|---|---|---|
| How does GitHub Actions reach Obs on the LAN? | A self-hosted runner container on the NAS | The runner connects outward; nothing on the LAN is exposed |
| How does GitHub reach Woodpecker for webhooks? | Not at first: trigger pipelines by hand (`woodpecker-cli`) or by polling | The NAS is LAN-only; a tunnel is a separate decision |
| Who may use the runner? | `main` and `workflow_dispatch` only, ephemeral, no Docker socket | This repo is public: a fork's pull request must not run on the NAS |
| Portainer or Arcane? | Run Arcane beside Portainer first; swap the deploy step later | Portainer is the CD engine today (`deploy-portainer` webhook, `tests/acceptance/test_05_portainer_cd.py`). Arcane's stack-deploy trigger is unconfirmed |

## Phases

1. **NAS baseline.** Docker on the NAS; `make up` for uFawkesPipe and uFawkesObs's stack, on one Docker network. Check whether Obs's existing `[self-hosted, synology]` runner is still alive.
2. **Runner.** A containerised, ephemeral GitHub runner with the trust limits above; the label stays `[self-hosted, synology]`.
3. **Real run.** One failing and one passing pipeline on a sample repo, with `dora_ingestion_url` pointing at the NAS's Obs. Record both 201 responses and the `first_commit_at` in the event. This closes AC-DORA-01 (#220) and the run in #123.
4. **Build.** Add the `registry_password` secret, then run `build-image` (the CNB step from ADR-006) once on the NAS.
5. **Arcane.** Deploy beside Portainer; use it for visibility. Decide the deploy-step replacement only once its trigger is confirmed.

## Verification Strategy

| Criterion | Evidence |
|---|---|
| AC-DORA-01 | Phase 3: both 201 responses and the stored event, recorded in `docs/ci-runner-image/verification-log.md` or the v2.0.0 plan |
| AC-PIPE-01 | Phase 4: a `build-image` run that pushes an image the next steps scan and sign |
| Runner safety | A fork's pull request does not start a job on the runner (tested on a throwaway fork) |
| Arcane | A deploy from the pipeline reaches the NAS without Portainer, before Portainer is removed |

## Out of scope

Kubernetes (the fawkes track), exposing the NAS to the internet, and changing the
runner image (`images/ci/`).
