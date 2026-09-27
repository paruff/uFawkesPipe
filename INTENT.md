# INTENT — Read This Before Touching Anything

**uFawkesPipe** is the CI/CD and security plane of the uFawkes suite. It's a
Docker Compose stack that includes:
- Woodpecker CI for pipelines, with a standard `.fawkespipe.yml` contract;
- SonarQube, Trivy, and Gitleaks for scanning;
- DefectDojo for scan results;
- Infisical and Falco, from the merged uFawkesSec;
- a Conftest/Rego `policy-check` step;
- Portainer for deploys.

It also publishes reusable GitHub workflows that other suite repos depend on.

## The one thing to know

**Run it standalone.** `make up` (`compose.yaml`) is self-contained, with its
own Postgres and Valkey. Suite mode (`make up-suite`) still points Woodpecker
at uFawkesRes's Postgres, and uFawkesRes is **deprecated**, so suite mode is
unsupported until #97 is fixed.

Two more things to know before building on it:
- **The `build-image` step is a placeholder** (see the README's stage table).
  Don't advertise Cloud Native Buildpacks image builds as working until it's
  real.
- **The version is ahead of the maturity.** Releases so far are
  `1.x.y-beta`, and no stable release exists. The first stable release is
  planned as `v2.0.0`, per the suite plan (AC-PIPE-01).

## Contracts other repos depend on

Treat these as public interfaces. Changing them breaks consumers outside this
repo:
- `.fawkespipe.yml` pipeline contract (`docs/pipeline-contract.md`)
- Reusable workflow inputs and outputs, which uFawkesObs and uFawkesDevX call.
  uFawkesDevX's `AGENTS.md` forbids modifying them from its side.
- DORA event emission to uFawkesObs (`contracts/dora-events/`,
  `docs/dora-contract.md`)

## Where this sits in the suite

| Plane | Repo |
|---|---|
| CI/CD + security | **uFawkesPipe** (this repo; merged uFawkesSec) |
| Observability | uFawkesObs (receives this repo's OTEL and DORA events) |
| Developer experience | uFawkesDevX (Score service triggers pipelines here) |
| Learning | uFawkesDojo (Yellow Belt targets this stack) |
| Kubernetes graduation track | fawkes (uses Tekton, not Woodpecker) |

The suite release plan is at
[uFawkes.dev `docs/ai-sdlc/suite-release/`](https://github.com/paruff/uFawkes.dev/tree/main/docs/ai-sdlc/suite-release).
This repo's first stable release is its Phase 2.

## What "done" means here

- **Planning follows the uFawkesAI artifact chain:**
  `docs/ai-sdlc/<feature>/intent.md` → `spec.md` (requirements and design) →
  `plan.md`. Today the planning docs are duplicated across the root and
  `docs/`: `specification.md`, `docs/specification.md`,
  `docs/product/spec.md`, `design.md`, `docs/design.md`, and
  `plan-for-the-day.md`. Consolidating them into `docs/ai-sdlc/v2.0.0/` is
  #96.
- **A feature is claimed only after a real pipeline run shows it working.**

## Explicit non-goals

- **Jenkins.** It was replaced by Woodpecker; the history is in
  `docs/history/jenkins-migration.md`.
- **Kubernetes deployment.** That's the fawkes track.
