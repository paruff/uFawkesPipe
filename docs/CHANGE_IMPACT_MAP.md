# Change Impact Map — uFawkesPipe

> uFawkesPipe is consumed by app teams via the `.fawkespipe.yml` pipeline contract.
> Changes here can break other teams' pipelines. Check this table before touching anything.

---

## Pipeline Contract (.fawkespipe.yml)

| If you change...                  | You must also update...                                                                       |
| --------------------------------- | --------------------------------------------------------------------------------------------- |
| Any field name                    | `examples/` — update all example files; `docs/` reference; migration guide for existing users |
| Required → optional or vice versa | `shared/` library steps that read the field; `validate.sh`                                    |
| Default values                    | `docs/` reference; `examples/`                                                                |
| Adding a new stage                | `shared/vars/` new step; `docs/ARCHITECTURE.md`; example `Jenkinsfile`                        |
| Removing a stage                  | Deprecation notice in `docs/`; migration path; `examples/`                                    |

---

## Jenkins Configuration (jenkins/)

| If you change...            | You must also update...                                                                      |
| --------------------------- | -------------------------------------------------------------------------------------------- |
| JCasC YAML structure        | Test with a fresh Jenkins container before merging                                           |
| Plugin list / versions      | Test full pipeline run on a branch; check for plugin compatibility conflicts                 |
| Seed job definitions        | Any manually-referenced job names in `docs/` or `examples/`                                  |
| Jenkins port (default 8080) | `docker-compose.yml` exposure; `scripts/` health checks; `README.md`; Obstackd scrape config |
| Jenkins agent configuration | `k8s/` agent pod templates if running on K8s                                                 |

---

## Shared Library (shared/)

| If you change...                    | You must also update...                                                   |
| ----------------------------------- | ------------------------------------------------------------------------- |
| A `vars/` step function signature   | All `Jenkinsfile` examples that call it in `examples/`; `docs/` reference |
| A step's DORA logging output format | `docs/METRICS.md` if metrics collection depends on log parsing            |
| Adding a new shared step            | `docs/API_SURFACE.md`; `docs/PROMPT_LIBRARY.md` if it's commonly used     |

---

## docker-compose.yml

| If you change...                   | You must also update...                                    |
| ---------------------------------- | ---------------------------------------------------------- |
| Jenkins image version              | Plugin compatibility check; test full pipeline             |
| Jenkins port                       | `scripts/`, health checks, `docs/`, `README.md`            |
| Jenkins home volume path           | Backup and restore procedures in `docs/RUNBOOKS.md`        |
| OTEL endpoint environment variable | `docs/` integration guide with Obstackd                    |
| Network name                       | Cross-plane integration with Obstackd if on shared network |

---

## Cross-Plane Impact

| If you change...              | Impact on other planes                                       |
| ----------------------------- | ------------------------------------------------------------ |
| OTEL exporter endpoint format | **Obstackd**: pipeline traces may stop arriving              |
| Jenkins webhook port          | **fawkes**: GitHub webhook configuration for the full IDP    |
| `.fawkespipe.yml` contract    | **developerd**: developer tooling that reads pipeline status |
| Pipeline stage names          | **Obstackd**: Grafana dashboards that filter by stage name   |
