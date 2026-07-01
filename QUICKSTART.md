# Quick Start Guide

Get uFawkesPipe v0.2 up and running in 5 minutes.

## Prerequisites

| Requirement | Version | Purpose |
|---|---|---|
| Docker | 20.10+ | Container runtime |
| Docker Compose | v2.0+ | Service orchestration (`docker compose` plugin) |
| RAM | 4GB+ | Woodpecker CI + SonarQube |
| GitHub OAuth App | — | Woodpecker authentication |
| DockerHub account | — | Container registry (username + access token) |

**Optional:**

| Requirement | Purpose |
|---|---|
| DefectDojo instance | Security scan ingestion (API token) |
| `pack` CLI | Cloud Native Buildpacks for local builds |
| uFawkesRes + uFawkesObs | Suite mode with PostgreSQL, OTEL telemetry |

**GitHub OAuth App setup:**

1. Go to <https://github.com/settings/developers> → OAuth Apps → New OAuth App
2. Set **Authorization callback URL** to `http://localhost:8000/authorize`
3. Note the **Client ID** and generate a **Client Secret**

**DockerHub access token:**

1. Go to <https://hub.docker.com/settings/security>
2. Click New Access Token
3. Copy the token for your `.env` file

## Installation

### Standalone Mode

Runs Woodpecker CI + SonarQube with SQLite/H2 storage — no external dependencies.

```bash
git clone https://github.com/paruff/uFawkesPipe.git
cd uFawkesPipe
make init          # creates .env from .env.example
nano .env          # fill in your credentials
make up            # start the stack
```

### Suite Mode

Connects to uFawkesRes (shared PostgreSQL, Valkey, Traefik) and uFawkesObs (OTEL Collector).

```bash
# Start dependencies first
cd ../uFawkesRes && make up
cd ../uFawkesObs && make up

# Then start uFawkesPipe in suite mode
cd ../uFawkesPipe
make init          # creates .env from .env.example
nano .env          # fill in your credentials (see Suite section below)
make up-suite      # start the stack with suite overlays
```

Wait 1-2 minutes for services to become healthy.

## Configuration

All settings live in `.env` (created from `.env.example` by `make init`).

### Core Variables

| Variable | Source | Description |
|---|---|---|
| `WOODPECKER_GITHUB_CLIENT` | GitHub OAuth App | Client ID |
| `WOODPECKER_GITHUB_SECRET` | GitHub OAuth App | Client Secret |
| `WOODPECKER_AGENT_SECRET` | Generate: `openssl rand -hex 32` | Shared secret between server and agent |
| `WOODPECKER_HOST` | Your hostname | Server URL (default: `http://localhost:8000`) |
| `SONARQUBE_ADMIN_PASSWORD` | Your choice | Admin password (change on first login) |
| `REGISTRY_USERNAME` | DockerHub | DockerHub username |
| `REGISTRY_TOKEN` | DockerHub | DockerHub access token |
| `DOJO_API_TOKEN` | DefectDojo (optional) | API token for security scan ingestion |

### Suite Mode Variables

| Variable | Source | Description |
|---|---|---|
| `POSTGRES_PASSWORD` | Must match uFawkesRes | Shared PostgreSQL password |
| `WOODPECKER_METRICS_TOKEN` | Your choice | Prometheus `/metrics` endpoint token |
| `UFAWKES_ENVIRONMENT` | Your choice | Environment label for OTEL events (default: `development`) |
| `OTEL_ENDPOINT` | uFawkesObs | OTEL Collector URL (e.g. `http://otel-collector:4318`) |
| `OTEL_HEADERS` | Optional | Auth headers for OTEL endpoint |

## Service Access

| Service | URL | Authentication |
|---|---|---|
| Woodpecker CI | <http://localhost:8000> | GitHub OAuth |
| SonarQube | <http://localhost:9001> | `admin` / `admin` (change on first login) |
| Portainer | <https://localhost:9443> | Create admin user on first visit |

## Create Your First Pipeline

### 1. Add `.fawkespipe.yml` to your repository

See `.fawkespipe.yml.example` for the full contract, or start with an example:

| Stack | Example |
|---|---|
| Node.js + Express | `examples/.fawkespipe-nodejs-express.yml` |
| Python + Flask | `examples/.fawkespipe-python-flask.yml` |
| Go | `examples/.fawkespipe-go.yml` |
| Java + Maven | `examples/.fawkespipe-java-maven.yml` |

### 2. Enable the repository in Woodpecker

1. Open <http://localhost:8000> and sign in with GitHub
2. Navigate to Repositories → Add repository
3. Find your repository and click Enable
4. Woodpecker auto-creates a GitHub webhook

### 3. Push code

```bash
git add .fawkespipe.yml
git commit -m "feat(ci): add pipeline contract"
git push
```

The pipeline triggers automatically via the GitHub webhook.

### 4. Monitor the pipeline

- Open <http://localhost:8000> → select your repository → view the pipeline run
- Pipeline stages: `init` → `secrets-scan` → `lint-yaml` → `lint-shell` → `validate-pipeline-contract` → `vuln-scan-fs` → `vuln-scan-image` → `upload-defectdojo` → `notify-obs`

## Smoke Test

Verify the installation is healthy:

```bash
# 1. Validate all configuration and contracts
make validate

# 2. Run unit tests
make test

# 3. Check Woodpecker health
curl -sf http://localhost:8000/healthz && echo "Woodpecker OK"

# 4. Check SonarQube health
curl -sf http://localhost:9001/api/system/status | grep -q '"status":"UP"' && echo "SonarQube OK"

# 5. Verify pipeline contract
make validate-docker
```

All commands should exit 0 with no errors.

## Common Commands

### Lifecycle

| Command | Description |
|---|---|
| `make init` | Create `.env` from `.env.example` |
| `make up` | Start stack (standalone) |
| `make up-suite` | Start stack (suite mode) |
| `make down` | Stop stack (standalone) |
| `make down-suite` | Stop stack (suite mode) |
| `make clean` | Remove test artifacts and stop containers |

### Observability

| Command | Description |
|---|---|
| `make logs` | View stack logs (standalone) |
| `make logs-suite` | View stack logs (suite mode) |
| `make status` | List running containers |
| `make status-suite` | List running containers (suite mode) |

### Validation

| Command | Description |
|---|---|
| `make validate` | Validate Docker + K8s + agents |
| `make validate-docker` | Validate `compose.yaml` |
| `make validate-suite` | Validate suite mode compose files |
| `make validate-k8s` | Validate Kubernetes manifests |
| `make validate-agents` | Validate agent and skill definitions |
| `make check-env` | Check required environment variables |

### Testing

| Command | Description |
|---|---|
| `make test` | Run all tests |
| `make test-unit` | Run unit tests |
| `make test-coverage` | Run tests with coverage report |

### Pre-commit

| Command | Description |
|---|---|
| `make pre-commit-setup` | Install pre-commit hooks |
| `make pre-commit-run` | Run hooks on all files |

## Troubleshooting

### Woodpecker won't start

```bash
# Check server logs
docker compose -f compose.yaml logs woodpecker-server

# Verify GitHub OAuth credentials in .env
grep WOODPECKER_GITHUB .env

# Verify agent secret matches
grep WOODPECKER_AGENT_SECRET .env
```

### Port 8000 already in use

```bash
# Find the process using port 8000
lsof -i :8000

# Kill it or change the port in compose.yaml
```

### GitHub webhook fails

- Verify `WOODPECKER_HOST` in `.env` matches the URL GitHub can reach
- For local development, use a tunnel tool (e.g. `ngrok`, `cloudflared`) to expose port 8000
- Check webhook delivery status in GitHub repository Settings → Webhooks

### SonarQube won't start

```bash
# Increase vm.max_map_count (Linux only)
sudo sysctl -w vm.max_map_count=262144

# Check logs
docker compose -f compose.yaml logs sonarqube
```

### OTEL Collector unreachable (suite mode)

```bash
# Verify OTEL_ENDPOINT in .env
grep OTEL_ENDPOINT .env

# Check uFawkesObs is running
cd ../uFawkesObs && make status

# Check connectivity from Woodpecker agent container
docker compose -f compose.yaml exec woodpecker-agent wget -qO- http://otel-collector:4318
```

## Next Steps

- Read the [Architecture Documentation](docs/ARCHITECTURE.md)
- Set up [Webhooks and APIs](docs/webhook-api.md)
- Plan [Kubernetes Promotion](docs/kubernetes-promotion.md)
- Review [Example Configs](examples/)
- Check [Known Limitations](docs/KNOWN_LIMITATIONS.md)

## Support

- Documentation: <https://github.com/paruff/uFawkesPipe>
- Issues: <https://github.com/paruff/uFawkesPipe/issues>
- Discussions: <https://github.com/paruff/uFawkesPipe/discussions>
