# Change Impact Map — uFawkesPipe

> uFawkesPipe is consumed by app teams via the `.fawkespipe.yml` pipeline contract.
> Changes here can break other teams' pipelines. Check this table before touching anything.

---

## Pipeline Contract (.fawkespipe.yml)

| If you change...                  | You must also update...                                                                       |
| --------------------------------- | --------------------------------------------------------------------------------------------- |
| Any field name                    | `examples/` — update all example files; `docs/` reference; migration guide for existing users |
| Required → optional or vice versa | `shared/` steps that read the field; `validate.sh`                                            |
| Default values                    | `docs/` reference; `examples/`                                                                |
| Adding a new stage                | `shared/` new step; `docs/ARCHITECTURE.md`; example `.woodpecker.yml`                        |
| Removing a stage                  | Deprecation notice in `docs/`; migration path; `examples/`                                    |

---

## Compose (standalone mode — compose.yaml)

| If you change...                                   | You must also update...                                                |
| -------------------------------------------------- | ---------------------------------------------------------------------- |
| Woodpecker image version                           | Check compatibility with `.woodpecker.yml` step images; test run       |
| Woodpecker port (8000 UI / 9000 gRPC)              | `.env.example`; `Makefile`; `docs/`; GitHub webhook URL               |
| SonarQube image version                            | Test SAST pipeline step; `docs/`                                      |
| SonarQube port (9001→9000)                         | `docs/`; user access instructions                                     |
| Portainer image version                            | Test Portainer webhook stack redeploy                                  |
| Portainer port (9443 HTTPS / 9002 edge)            | `docs/`; user access instructions                                     |
| Volume names                                       | `make down -v` would lose data; document backup                       |
| Network name (`ufawkespipe_default`)               | `compose.suite.yaml` reference; step container network configuration   |

---

## Compose (suite mode — compose.suite.yaml)

| If you change...                                   | You must also update...                                                |
| -------------------------------------------------- | ---------------------------------------------------------------------- |
| External network name (`fawkes-backbone-net`)      | Must match uFawkesRes `compose.yaml` network name                     |
| External network name (`observability-lab`)         | Must match uFawkesObs `compose.yaml` network name                     |
| PostgreSQL connection string for Woodpecker        | Must match uFawkesRes `compose.yaml` credentials                      |
| PostgreSQL connection string for SonarQube         | Must match uFawkesRes `compose.yaml` credentials                      |
| OTEL exporter endpoint                            | Must match uFawkesObs `compose.yaml` OTEL collector address          |
| OTEL exporter protocol                            | Must match uFawkesObs collector receiver config                       |
| `WOODPECKER_PROMETHEUS_AUTH_TOKEN` format          | Must match Prometheus scrape config in uFawkesObs                     |

---

## Pipeline Definition (.woodpecker.yml)

| If you change...                    | You must also update...                                                   |
| ----------------------------------- | ------------------------------------------------------------------------- |
| Pipeline step names                 | `docs/ARCHITECTURE.md` step table; uFawkesObs Grafana dashboards          |
| `notify-obs` event format           | uFawkesObs OTEL log parsing; `docs/` telemetry reference                  |
| Structured JSON log format           | uFawkesObs Alloy log parsing config; `docs/` logging reference            |
| Adding or removing a step           | `docs/ARCHITECTURE.md`; test pipeline contract validation                 |
| Security scan severity thresholds   | `docs/`; team notification about changed gate                            |

---

## Cross-Plane Impact

| If you change...                    | Impact on other planes                                             |
| ----------------------------------- | ------------------------------------------------------------------ |
| OTEL exporter endpoint format       | **uFawkesObs**: pipeline traces/metrics/logs may stop arriving     |
| OTEL exporter protocol (gRPC→HTTP)  | **uFawkesObs**: collector receiver config must match               |
| Shared network name (`fawkes-backbone-net`) | **uFawkesRes**: must create network; **uFawkesSec**, **uFawkesDevX**: must attach |
| Shared network name (`observability-lab`)    | **uFawkesObs**: must create network; telemetry won't flow          |
| Woodpecker PostgreSQL connection     | **uFawkesRes**: `fawkes-postgres:5432` must accept the connection  |
| SonarQube PostgreSQL connection       | **uFawkesRes**: `fawkes-postgres:5432` must have `sonar` database  |
| `.fawkespipe.yml` contract           | **developerd**: developer tooling that reads pipeline status       |
| Pipeline stage names                 | **uFawkesObs**: Grafana dashboards that filter by stage name       |
| Deployment event format              | **uFawkesObs**: DORA metrics pipeline that consumes deployment events |
| Woodpecker webhook port (8000)        | **fawkes**: GitHub webhook configuration for the full IDP          |
