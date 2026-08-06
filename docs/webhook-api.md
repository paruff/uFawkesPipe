# Webhook and API Documentation

uFawkesPipe exposes Woodpecker CI webhooks and APIs that allow external planes to trigger and interact with pipelines.

> **Stack:** Woodpecker CI (v3) is the pipeline engine. The legacy Jenkins REST API and
> Generic Webhook Trigger plugin were removed with the Jenkins stack — see
> `docs/history/jenkins-migration.md`.

## Overview

The platform provides:

1. **GitHub Webhooks** — Automatic pipeline triggers from GitHub push / pull request
2. **Woodpecker REST API** — Programmatic pipeline control (list, trigger, query)
3. **Woodpecker CLI** — `woodpecker-cli` for interactive / scripted control
4. **Portainer Webhook (CD)** — Stack redeploy via Portainer webhook URL

---

## 1. GitHub Webhooks

Woodpecker automatically registers a webhook on each GitHub repository when the
repository is activated in the Woodpecker UI.

### Endpoint

```
POST http://<woodpecker-host>:8000/api/hooks/<repository-id>
```

- **Payload URL:** `http://<woodpecker-host>:8000/api/hooks/<repository-id>`
- **Content type:** `application/json`
- **Events:** Push, Pull Request

The webhook is **configured automatically** during repository activation — no
manual GitHub webhook setup is required.

### Pipeline Configuration

Pipelines are declared in `.woodpecker.yml` at the repository root (app teams
configure them via the `.fawkespipe.yml` contract). Woodpecker triggers the
matching pipeline on push / PR events.

---

## 2. Woodpecker REST API

Woodpecker serves a REST API on the server port.

### Base URL

```
http://<woodpecker-host>:8000/api
```

### Health Check

```
GET http://<woodpecker-host>:8000/healthz
```

Returns `200` when the server is healthy (used by the acceptance suite and
container healthchecks).

### Authentication

API access uses a Woodpecker API token. Generate one from the Woodpecker UI
(user settings → tokens) and send it as a bearer token:

```bash
curl -H "Authorization: Bearer <woodpecker-api-token>" \
  "http://localhost:8000/api/user"
```

### Common Endpoints

| Endpoint | Purpose |
| -------- | ------- |
| `GET /api/user` | Current user / token validity |
| `GET /api/repos` | List repositories |
| `GET /api/repos/{owner}/{repo}/pipelines` | List pipelines for a repo |
| `GET /api/repos/{owner}/{repo}/pipelines/{number}` | Get pipeline status / logs |

See the [Woodpecker API documentation](https://woodpecker-ci.org/docs/api) for
the full endpoint reference.

---

## 3. Woodpecker CLI

The `woodpecker-cli` binary provides the same operations from the command line.

```bash
# List repositories and pipelines
woodpecker-cli repo ls
woodpecker-cli repo info <org/repo>
woodpecker-cli pipeline ls --repo <org/repo>

# Trigger a specific pipeline
woodpecker-cli pipeline start <org/repo> <pipeline-number>
```

See [Woodpecker CLI documentation](https://woodpecker-ci.org/docs/cli) for full usage.

---

## 4. Portainer Webhook (CD)

Deployments use a **Portainer stack webhook**: a POST to the Portainer webhook
URL triggers a stack redeploy with the latest image.

### Endpoint

```
POST <portainer-webhook-url>
```

The webhook URL is provided as the `PORTAINER_WEBHOOK_URL` secret (Woodpecker
secret store / `.env`) and is called by the pipeline's CD step after a
successful publish.

---

## Build Status API

Pipeline status can be queried via the Woodpecker API or CLI (Section 2 / 3
above). Pipeline events are also exported to uFawkesObs via OTEL for DORA
metrics — see `docs/ARCHITECTURE.md` §7 (Telemetry).
