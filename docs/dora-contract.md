# uFawkesPipe ⇄ uFawkesObs Contract Reference

**Version:** 1.1.0 (schema versions tracked independently — see below)

uFawkesPipe hosts the suite-wide, machine-readable source of truth for
**everything this repo sends to uFawkesObs**: the DORA event JSON Schemas
(deployment, PR, incident, rework — via REST) and the OTLP telemetry
conventions (traces, metrics, logs). The DORA schemas live in
[`contracts/dora-events/`](../contracts/dora-events/); this document is the
human-readable companion for both channels.

> **Quick start:** the four DORA schemas, a versioning policy, and a full
> field reference are in [`contracts/dora-events/README.md`](../contracts/dora-events/README.md).
> This document covers *where the DORA contract came from*, *who consumes
> it*, *how uFawkesPipe emits both DORA events and OTLP telemetry*, and
> *what each channel is actually for* — none of which duplicates the schema
> reference.

---

## Table of Contents

- [Origin and scope](#origin-and-scope)
- [Who consumes this contract today](#who-consumes-this-contract-today)
- [How uFawkesPipe emits DORA events](#how-ufawkespipe-emits-dora-events)
- [OTLP telemetry contract (traces, metrics, logs)](#otlp-telemetry-contract-traces-metrics-logs)
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

## How uFawkesPipe emits DORA events

**Fixed in PR #70** (2026-08-18). `notify-obs` (`.woodpecker.yml`) now sends
**two independent, non-blocking** payloads on every successful push to
`main`:

1. A `POST` to `${DORA_INGESTION_URL}/event` with a JSON body matching
   `contracts/dora-events/deployment-event.schema.json` exactly — this is
   what actually feeds DORA metrics computation. Requires the
   `dora_ingestion_url` Woodpecker secret (`http://<obs-host>:8088`
   typically); `dora_api_key` is optional bearer auth, sent only if
   configured.
2. The original OTLP trace span to `${OTEL_ENDPOINT}/v1/traces` — unchanged,
   still useful for tracing in Tempo, but **not** a DORA signal (see below).

Before PR #70, only (2) existed, and it was never validated against
`deployment-event.schema.json` or reached uFawkesObs's `dora/ingestion/`
REST API — deployments did not count toward DORA metrics at all. That gap,
first documented here, is what PR #70 closed.

**Only the `deployment` event type is wired up.** `pr`, `incident`, and
`rework` events are not — this repo's Woodpecker pipeline doesn't have a
verified, unambiguous trigger distinguishing "PR merged" from "PR
opened/synced" in its current event vocabulary (`when: event:
[push, pull_request]` doesn't disambiguate this), and guessing at that
mapping risks feeding wrong data into lead-time calculations. Open follow-up,
not attempted.

`docs/ARCHITECTURE.md` §12.4's telemetry diagram labels the OTLP HTTP path
to `otel-collector:4318` as "Deployment events" / "Events" — that labeling
predates this fix and is misleading for DORA purposes specifically: the
OTLP path is real and still used (see next section), but the DORA event
that actually reaches `dora/ingestion/` travels over REST to a different
port (`8088`) entirely. `docs/ARCHITECTURE.md` itself is not corrected
here (out of scope for this doc).

## OTLP telemetry contract (traces, metrics, logs)

Separate from the DORA event contract above, uFawkesPipe sends general
observability telemetry to uFawkesObs's OTel Collector in suite mode (per
`docs/ARCHITECTURE.md` §7 and §12.4). Two independent sources:

| Source | Protocol | Target | Content |
| --- | --- | --- | --- |
| `woodpecker-server` (continuous, while the server runs) | OTLP gRPC | `otel-collector:4317` | Traces + metrics + logs |
| `notify-obs` step (once per successful `main` push) | OTLP HTTP | `otel-collector:4318` | A single `deployment` trace span — see below |
| `woodpecker-server` `/metrics` endpoint | Prometheus scrape (pull, not OTLP) | uFawkesObs's Prometheus | Pipeline-level metrics (`WOODPECKER_METRICS_TOKEN`-gated) |

**Resource attribute convention:** the `notify-obs` OTLP span sets
`service.name: "ufawkespipe"` on its resource attributes — this is the
convention any future OTLP-emitting step in this repo should follow, so
uFawkesObs's Tempo/Grafana can attribute spans back to this repo
consistently. `woodpecker-server`'s own resource attributes are set by
Woodpecker itself, not by this repo's pipeline config — not independently
verified here.

**What the `notify-obs` span currently contains** (see `.woodpecker.yml`
for the exact payload): `service.name`, `deployment.environment`,
`deployment.version` (short SHA), `deployment.status` on the resource;
`git.commit.sha` (full), `git.branch`, `pipeline.duration_ms` on the span.
This is informational tracing data only — as covered above, it is not what
feeds DORA metrics.

**Standalone mode has none of this.** Per `docs/ARCHITECTURE.md` §12.3,
OTLP/Prometheus/Alloy wiring only applies when uFawkesPipe runs alongside
uFawkesObs ("suite mode"); standalone, `notify-obs`'s OTLP send is a no-op
(`OTEL_ENDPOINT` unset → skipped, per the existing `dora_warn` branch) and
metrics/logs stay local (stdout / Docker json-file).

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
