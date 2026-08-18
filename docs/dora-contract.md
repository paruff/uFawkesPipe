# DORA Event Contract Reference

**Version:** 1.0.0 (schema versions tracked independently — see below)

uFawkesPipe hosts the suite-wide, machine-readable source of truth for the
DORA event contract: the JSON Schemas any CI/CD system uses to report
deployment, PR, incident, and rework events for DORA metrics computation.
The schemas themselves live in
[`contracts/dora-events/`](../contracts/dora-events/); this document is the
human-readable companion.

> **Quick start:** the four schemas, a versioning policy, and a full field
> reference are in [`contracts/dora-events/README.md`](../contracts/dora-events/README.md).
> This document covers *where the contract came from*, *who currently
> consumes it*, and *how uFawkesPipe's own pipelines should emit events
> against it* — none of which duplicates the schema reference.

---

## Table of Contents

- [Origin and scope](#origin-and-scope)
- [Who consumes this contract today](#who-consumes-this-contract-today)
- [How uFawkesPipe should emit DORA events](#how-ufawkespipe-should-emit-dora-events)
- [Known gap: no automated sync with uFawkesObs](#known-gap-no-automated-sync-with-ufawkesobs)
- [Where the human-readable page goes next](#where-the-human-readable-page-goes-next)

---

## Origin and scope

These schemas are a verbatim copy of `dora/events/*.schema.json` from
[uFawkesObs](https://github.com/paruff/uFawkesObs), as of its PR #227
(merged 2026-08-18, `docs/CONTRACTS.md`). uFawkesObs's own `dora/ingestion/`
service consolidated what used to be a separate `uFawkesDORA` repo, and its
`docs/CONTRACTS.md` documented this as uFawkesObs's *consumer-side* view of
the contract, noting the long-term plan for uFawkesPipe to host the shared
version instead — this is that move.

**uFawkesObs remains the reference implementation.** It's the service that
actually validates incoming events (`dora/ingestion/api/validator.py`,
`EVENT_TYPE_SCHEMA_MAP`) and computes the five DORA metrics from them. This
repo hosting the schemas doesn't change where events get processed — it
only centralizes where the contract is authored and discovered.

## Who consumes this contract today

Concrete, working examples of the contract in executable form live in
uFawkesObs's `dora/collectors/` directory (not duplicated here to avoid a
second copy going stale):

- `dora/collectors/github/dora-deployment-event.yml` and
  `dora-pr-event.yml` — reusable GitHub Actions workflows.
- `dora/collectors/generic/curl-examples.sh` — raw `curl` examples for all
  four event types, with a field-mapping table for GitLab CI, CircleCI,
  Jenkins, and Woodpecker CI variable names.
- `dora/collectors/woodpecker/pipeline-snippet.yml` — a Woodpecker-specific
  step, directly relevant to this repo's own pipeline engine.
- `dora/collectors/manual-incident/` — scripts for manually emitted
  `incident` events outside of CI.

Events are POSTed as JSON to uFawkesObs's ingestion API:

| Method | Path           | Purpose                                                |
| ------ | -------------- | ------------------------------------------------------- |
| `POST` | `/event`       | One event, validated against the matching schema, `201` on success. |
| `POST` | `/event/batch` | Multiple events, all-or-nothing.                        |

Default address: `http://<obs-host>:8088` (uFawkesObs's `dora-api` service,
`dora` compose profile — see uFawkesObs's `AGENTS.md` §10 and
`compose.yaml`). **No authentication is currently enforced** on that
endpoint as of uFawkesObs PR #227's writing (a documented gap there, not
implemented here or anywhere in the suite yet).

## How uFawkesPipe should emit DORA events

**This repo's own `notify-obs` pipeline step (`.woodpecker/steps/common.yaml`)
does not currently use this contract.** It sends a `deployment` event as a
generic OTLP trace span — `POST ${OTEL_ENDPOINT}/v1/traces` with a
`resourceSpans` payload — to uFawkesObs's OTel Collector. That lands as an
ordinary trace in Tempo. It is **not** validated against
`deployment-event.schema.json`, does not reach uFawkesObs's `dora/ingestion/`
REST API, and does not feed DORA metrics computation at all.

This is a real, previously-undocumented gap discovered while writing this
doc, not something fixed here (out of scope for a docs-only change — flagging
it for whoever picks up the actual pipeline step change): to make
uFawkesPipe's deployments actually count toward DORA metrics, `notify-obs`
(or a new step) needs to `POST` a JSON body matching
`contracts/dora-events/deployment-event.schema.json` to uFawkesObs's
`/event` REST endpoint instead of (or in addition to) the current OTLP
trace span. `docs/ARCHITECTURE.md` §12.4's telemetry diagram documents the
OTLP path as the deployment-event mechanism today — that diagram is now
known to be aspirational/incorrect for DORA purposes specifically (OTLP
traces/metrics/logs still work fine for their own purpose; only the
DORA-event claim is wrong) and should be corrected once the actual emission
path is fixed.

## Known gap: no automated sync with uFawkesObs

There is currently **no CI check, tooling, or process** keeping this repo's
`contracts/dora-events/*.schema.json` and uFawkesObs's `dora/events/*.schema.json`
in sync — they are two independent copies. A change made in one and not the
other will silently diverge: uFawkesObs's copy is what its `dora/ingestion/`
service actually enforces at runtime, regardless of what this repo says.
Until a sync mechanism exists (e.g., a scheduled diff check, or uFawkesObs
vendoring these schemas from here as a submodule/package), treat this repo's
copy as the *documentation* source of truth and uFawkesObs's copy as the
*enforcement* source of truth, and manually port any change between them
(see `contracts/dora-events/README.md`'s Contributing section).

## Where the human-readable page goes next

Per the suite's documented plan (uFawkesObs `docs/CONTRACTS.md`),
**ufawkes.dev** is expected to eventually render a human-readable contracts
page sourced from this repo's `contracts/dora-events/` — not implemented
here. This document and the schema files are the machine-readable/authored
source that page would draw from.
