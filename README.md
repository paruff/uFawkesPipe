# uFawkesPipe

[![CI Pipeline](https://github.com/paruff/uFawkesPipe/actions/workflows/ci-pipeline.yml/badge.svg)](https://github.com/paruff/uFawkesPipe/actions/workflows/ci-pipeline.yml) [![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

**Integration & Delivery Plane of the Fawkes IDP Family**

uFawkesPipe is a Woodpecker CI-based CI/CD platform with integrated SAST (SonarQube, Trivy, Gitleaks), Cloud Native Buildpacks, and DefectDojo security scan ingestion — the CI/CD plane of the Fawkes IDP.

## 🚀 Features

- **Polyglot Support** - Build applications in Java, Python, Node.js, Go, Ruby, and more via Cloud Native Buildpacks
- **Standard Pipeline Contract** - Define CI/CD behavior via `.fawkespipe.yml` configuration (see [docs/pipeline-contract.md](docs/pipeline-contract.md))
- **Cloud Native Buildpacks** - Build OCI-compliant container images without Dockerfiles
- **Security-First Pipeline** - Integrated Gitleaks secret scanning, Trivy vulnerability scanning (filesystem + container), and SonarQube SAST
- **DefectDojo Integration** - Automated security scan result ingestion post-build
- **Woodpecker-based** - Lightweight, YAML-driven CI/CD orchestration with GitHub OAuth
- **DORA Observability** - Structured JSON logging, OTEL deployment event emission, Prometheus metrics
- **Standalone + Suite Mode** - Run independently or connect to uFawkesRes (PostgreSQL/Traefik) and uFawkesObs (OTEL/Loki)
- **Security Plane (merged from uFawkesSec)** - DefectDojo, Infisical, Trivy server, and Falco run alongside the CI/CD stack, plus a Conftest/Rego `policy-check` pipeline step — see [Security Plane](#-security-plane) below

## 📋 Pipeline Stages

Every pipeline in uFawkesPipe follows these standardized stages (defined in [`.woodpecker.yml`](.woodpecker.yml)):

| # | Stage | Steps | Parallel | Branch Gate |
|---|-------|-------|----------|-------------|
| 1 | **validate** | `init` → `lint-yaml` + `lint-shell` | Yes (lint) | None |
| 2 | **test** | `unit-tests` + `integration-tests` + `contract-tests` | Yes | None |
| 3 | **security** | `secrets-scan` → `vuln-scan-fs` → `vuln-scan-image` | Sequential | `vuln-scan-image`: main only |
| 4 | **build** | `build-image` | — | main only |
| 5 | **publish** | `upload-defectdojo` | — | main only |
| 6 | **deploy** | `notify-obs` | — | main only |

**Step details:**

- **init** — Create artifact directories (security, coverage, tests)
- **lint-yaml** — Validate `compose.yaml`, `.woodpecker.yml`, `.env.example` with yamllint
- **lint-shell** — ShellCheck validation on `scripts/*.sh` and `validate.sh`
- **unit-tests** — Fast, isolated pytest unit tests (no external deps)
- **integration-tests** — Cross-component tests (may require Docker)
- **contract-tests** — Pipeline contract, compose, and YAML validation
- **secrets-scan** — Hard gate: Gitleaks secret detection with `.gitleaks.toml` rules
- **vuln-scan-fs** — Trivy filesystem vulnerability scan (entire working tree)
- **vuln-scan-image** — Trivy container image vulnerability scan (main branch only)
- **build-image** — Container image build via CNB (placeholder)
- **upload-defectdojo** — Collect Gitleaks + Trivy results and POST to DefectDojo API (non-blocking)
- **notify-obs** — Emit structured deployment event to uFawkesObs OTEL collector (non-blocking)

All steps emit structured JSON logs via `scripts/dora-log.sh` compatible with uFawkesObs/Loki ingestion.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    uFawkesPipe Platform                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Woodpecker Server  │  │  SonarQube   │  │  Portainer   │  │
│  │ + Agent            │  │   (SAST)     │  │   CE (CD)    │  │
│  │                    │  │              │  │              │  │
│  │  - Pipeline YAML   │  │  - Quality   │  │  - Stacks    │  │
│  │  - GitHub OAuth    │  │    Gates     │  │  - Secrets   │  │
│  │  - CLI triggers    │  │  - Coverage  │  │  - Volumes   │  │
│  └────────────────────┘  └──────────────┘  └──────────────┘  │
│         │                          │                │      │
│         └──────────────────────────┴────────────────┘      │
│                           │                                 │
│                  ┌────────▼────────┐                        │
│                  │  CNB Builder    │                        │
│                  │  (Buildpacks)   │                        │
│                  └────────┬────────┘                        │
│                           │                                 │
│                           ▼                                 │
│                  ┌─────────────────┐                        │
│                  │   Docker        │                        │
│                  │   Registry      │                        │
│                  └─────────────────┘                        │
│                                                               │
│  Suite mode: ┌────────────┐   ┌───────────────────┐         │
│              │ uFawkesRes │   │   uFawkesObs      │         │
│              │ (Postgres, │◄──│ (OTEL, Loki,      │         │
│              │  Traefik)  │   │  Prometheus)      │         │
│              └────────────┘   └───────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

- **Standalone mode** (`make up`): Woodpecker + SonarQube + Portainer, local storage
- **Suite mode** (`make up-suite`): Adds uFawkesRes PostgreSQL, Valkey, Traefik ingress and uFawkesObs OTEL Collector, Alloy, Loki, Prometheus

## 🔐 Security Plane

The security plane (formerly the standalone uFawkesSec repo) is merged into this
repo's `compose.yaml` / `compose.suite.yaml` and runs alongside the CI/CD stack:

| Service                    | Image                                  | Role                                    |
| --------------------------- | --------------------------------------- | ---------------------------------------- |
| `defectdojo`                | `defectdojo/defectdojo-django:2.38.0`   | Security findings aggregation (Django)   |
| `defectdojo-nginx`          | `defectdojo/defectdojo-nginx:2.38.0`    | Reverse proxy for DefectDojo             |
| `defectdojo-celery-beat`    | `defectdojo/defectdojo-django:2.38.0`   | Periodic task scheduler                  |
| `defectdojo-celery-worker`  | `defectdojo/defectdojo-django:2.38.0`   | Async task worker                        |
| `infisical`                 | `infisical/infisical:v0.93.1-postgres`  | Zero-trust secrets store                 |
| `trivy-server`               | `aquasec/trivy:0.74.0`                  | Shared Trivy CVE cache server            |
| `falco`                      | `falcosecurity/falco-no-driver:0.39.2`  | Runtime container security monitoring    |

Standalone mode embeds its own `postgres`/`valkey`; suite mode (`compose.suite.yaml`)
redirects these services to uFawkesRes's shared `fawkes-postgres`/`fawkes-cache`
instead. Rego policies live in `policy/` and run as the `policy-check` pipeline
step (see [docs/policy-guide.md](docs/policy-guide.md)).

## 🛠️ Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose v2.0+ (`docker compose` plugin, not standalone `docker-compose`)
- 4GB+ RAM available for containers
- GitHub OAuth App (Client ID + Secret) for Woodpecker authentication
- DockerHub account (for image registry)

### Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/paruff/uFawkesPipe.git
   cd uFawkesPipe
   ```

2. **Configure environment**

   ```bash
   cp .env.example .env
   # Edit .env with your credentials and OAuth keys
   nano .env
   ```

3. **Start the platform**

   ```bash
   # Standalone mode (Woodpecker + SonarQube + Portainer)
   make up

   # Or suite mode (connects to uFawkesRes + uFawkesObs)
   make up-suite
   ```

4. **Access the platform**

   | Service       | Port | URL                    | Auth                     |
   | ------------- | ---- | ---------------------- | ------------------------ |
   | Woodpecker CI | 8000 | http://localhost:8000  | GitHub OAuth             |
   | Portainer CE  | 9443 | https://localhost:9443 | Admin account (first use)|
   | SonarQube     | 9000 | http://localhost:9000  | admin / (from .env)      |

### First Pipeline

1. Add a `.fawkespipe.yml` to your application repository (see [docs/pipeline-contract.md](docs/pipeline-contract.md))
2. Push to GitHub
3. In Woodpecker UI: Repositories → Activate your repository
4. Push code → Pipeline auto-triggers via GitHub webhook

Full details: [QUICKSTART.md](QUICKSTART.md)

## 📖 Pipeline Contract Reference

The `.fawkespipe.yml` file is the standard pipeline contract that defines how your application is built, tested, scanned, and deployed. It is placed at the root of your application repository.

### Key Sections

- **`app`** - Application metadata (name, type, language, version)
- **`build`** - Build configuration: `cnb` (Cloud Native Buildpacks), `docker`, or `custom`
- **`stages`** - Enable/disable and configure pipeline stages (lint, test, sast, dependency_scan, build, image_scan, push)
- **`notifications`** - Slack and email notification configuration
- **`kubernetes`** - Kubernetes deployment configuration (promotion path)
- **`advanced`** - Timeout, retry, parallel execution, artifact retention

### Language-Specific Examples

- [Java/Maven](examples/.fawkespipe-java-maven.yml)
- [Python/Flask](examples/.fawkespipe-python-flask.yml)
- [Node.js/Express](examples/.fawkespipe-nodejs-express.yml)
- [Go](examples/.fawkespipe-go.yml)

**Full reference: [docs/pipeline-contract.md](docs/pipeline-contract.md)**

## 🔌 Webhook API

uFawkesPipe exposes Woodpecker CI webhooks for external plane integration.

### Trigger Pipeline via Webhook

Woodpecker CI automatically receives push webhooks from GitHub when a repository is activated. The webhook URL is auto-configured by Woodpecker during repository activation.

**GitHub Webhook Integration**:

Configured automatically when you activate a repository in Woodpecker. The webhook points to:

- Payload URL: `http://<woodpecker-host>:8000/api/hooks/<repository-id>`
- Content type: `application/json`
- Events: Push, Pull Request

### CLI Commands

**Woodpecker CLI** triggers from the command line:

```bash
# List repositories and pipelines
woodpecker-cli repo ls
woodpecker-cli repo info <org/repo>
woodpecker-cli pipeline ls --repo <org/repo>

# Trigger a specific pipeline
woodpecker-cli pipeline start <org/repo> <pipeline-number>
```

See [Woodpecker CLI documentation](https://woodpecker-ci.org/docs/cli) for full usage.

## ☸️ Kubernetes Promotion Path

uFawkesPipe is designed for single-node development with Docker Compose. Kubernetes deployment support is planned but not yet implemented for the Woodpecker stack.

See the [`kubernetes` section](docs/pipeline-contract.md#kubernetes---kubernetes-deployment) in the pipeline contract for the planned configuration schema.

## 🔒 Security Features

### Secret Detection

- **Gitleaks** — Single secret-scanning tool (hard gate): scans all files for secrets, API keys, and credentials on every commit/push
- **Config** — `.gitleaks.toml` allowlist for test fixtures / placeholders; runs in pre-commit, Woodpecker CI, and GitHub Actions

### Static Application Security Testing (SAST)

- **SonarQube** — Code quality and security vulnerability analysis
- **Trivy** — Filesystem and code vulnerability scanning

### Dependency Scanning

- **Trivy** — Comprehensive vulnerability database scanning (filesystem and container image)
- **OWASP Dependency-Check** — Known vulnerable dependencies (configured in `.fawkespipe.yml`)

### Container Security

- **Trivy** — Container image vulnerability scanning (main branch only)
- **Cloud Native Buildpacks** — Build OCI images without Dockerfiles (reduces attack surface)
- **Image pinning** — All service images pinned to specific versions (no `:latest`)

### DefectDojo Integration

- Automated upload of Gitleaks and Trivy scan results to DefectDojo API
- Non-blocking — scan ingestion failure does not fail the pipeline

## 🧪 Test Coverage

The `tests/unit/` suite validates the `.woodpecker.yml` pipeline definition statically — it does **not** execute the pipeline against a live Woodpecker instance. End-to-end pipeline execution is verified manually via `make up` + Woodpecker UI.

### What `pytest tests/unit/` Verifies

| Test Module | Coverage |
|-------------|----------|
| `test_woodpecker_yml.py` | **Pipeline structure**: Valid YAML, `steps` list exists, `when` section present. **Step ordering**: `init` first, lint before security, test before security. **Step configuration** (per step): correct image & version pinning (e.g., `alpine:3.20`, `zricethezav/gitleaks:v8.18.2`, `curlimages/curl:8.6.0`), required commands/flags (`--format json`, `--no-progress`, `--exit-code=1` for secrets), output paths (`artifacts/security/*.json`), secret wiring (`from_secret`), branch conditions (`when: branch: main`), DORA logging (`source dora-log.sh`, `dora_start`, `dora_emit`), non-blocking behavior (`dora_warn` on failure). **Artifact directories**: `init` creates `artifacts/security`, `artifacts/coverage`, `artifacts/tests` via `mkdir -p`. |
| `test_docker_compose_validation.py` | **Compose structure**: Valid YAML, `services` section, all services have `image`, no `:latest` tags, all services have `labels`, volume declarations exist, named volumes (no host paths), no secrets in compose. **Healthchecks**: Services declare `healthcheck` (except `dependency-check`, `pack-cli`). |
| `test_compose_network.py` | **Standalone mode**: `compose.yaml` declares NO `fawkes-net`, no services attach to it, `woodpecker-agent` has no `WOODPECKER_BACKEND_DOCKER_NETWORK`. **Suite mode**: `compose.suite.yaml` declares `fawkes-net` as `external: true` with `name: fawkes-net`, all 4 services attach, agent has `WOODPECKER_BACKEND_DOCKER_NETWORK=fawkes-net`. **Makefile**: `network` target creates `fawkes-net` idempotently (double-pipe true); `up` has NO `network` dep; `up-suite` HAS `network` dep. |
| `test_artifact_dirs.py` | **Init step**: First step is `init` with `alpine:3.20`; commands include `mkdir -p artifacts/security`, `artifacts/coverage`, `artifacts/tests` using `mkdir -p`. |

### What Unit Tests Do NOT Cover

- ❌ Live pipeline execution against Woodpecker server
- ❌ GitHub webhook delivery / repository activation flow
- ❌ Docker image build / CNB buildpack execution
- ❌ SonarQube quality gate evaluation
- ❌ DefectDojo API ingestion
- ❌ OTEL collector event emission / Loki ingestion
- ❌ Cross-service integration (Woodpecker ↔ SonarQube ↔ Portainer)
- ❌ Performance / load characteristics

### Running Tests

```bash
# All unit tests (fast, no external deps)
python3 -m pytest tests/unit/ -v

# With markers (unit, integration, smoke, acceptance)
python3 -m pytest tests/ -m unit
python3 -m pytest tests/ -m integration
python3 -m pytest tests/ -m smoke
python3 -m pytest tests/ -m acceptance
```

## 🔧 Configuration

### Pipeline Configuration

The CI pipeline is defined in [`.woodpecker.yml`](.woodpecker.yml). Customize it to:

- Add or remove pipeline steps
- Configure environment variables for different stages
- Define secrets for registry authentication and API tokens

### Pipeline Contract Configuration

Application teams configure their pipeline behavior via `.fawkespipe.yml` at the root of their repository. See [docs/pipeline-contract.md](docs/pipeline-contract.md) for the full reference.

### Service Configuration

Edit [`compose.yaml`](compose.yaml) to:

- Change exposed ports
- Add more services
- Configure resource limits
- Add additional networks

### Volume Management

Persistent data is stored in Docker volumes:

- `woodpecker_data` — Woodpecker CI database and config
- `portainer_data` — Portainer CD data
- `sonarqube_data` — SonarQube analysis data
- `pack_cache` — CNB build cache

**Backup volumes:**

```bash
docker run --rm -v ufp_woodpecker_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/woodpecker-backup.tar.gz -C /data .
```

## 🐛 Troubleshooting

### Woodpecker won't start

```bash
# Check logs
make logs

# Check Woodpecker status
make status

# Verify GitHub OAuth config in .env
grep WOODPECKER_GITHUB .env

# Reset Woodpecker data
make down
docker volume rm ufp_woodpecker_data
make up
```

### Port 8000 (or 9000, 9443) already in use

```bash
lsof -i :8000
lsof -i :9000
lsof -i :9443
```

Edit `compose.yaml` to change the host port mapping if needed.

### SonarQube won't start

```bash
# Check logs
make logs sonarqube

# Increase vm.max_map_count (required for Elasticsearch)
sudo sysctl -w vm.max_map_count=262144

# Make permanent
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```

### GitHub webhook fails

- Verify `WOODPECKER_HOST` in `.env` matches the webhook callback URL
- Check Woodpecker UI → Repositories → your repo → Settings for webhook status
- Ensure your Woodpecker instance is reachable from GitHub

### OTEL collector unreachable (suite mode)

```bash
# Verify OTEL endpoint is set
grep OTEL_ENDPOINT .env

# Check connectivity from Woodpecker agent container
docker compose -f compose.yaml exec woodpecker-agent wget -qO- http://otel-collector:4318
```

### Pack build fails

```bash
# Check Docker access
docker ps

# Verify builder image
docker pull paketobuildpacks/builder:base

# Check pack logs in Woodpecker CI build output
```

### Trivy scan is slow

- First run downloads CVE database (1-5 minutes)
- Subsequent runs use cached data (faster)
- Trivy image scan runs only on main branch pushes

## 📚 Additional Resources

- [Woodpecker CI Documentation](https://woodpecker-ci.org/docs/intro)
- [Cloud Native Buildpacks](https://buildpacks.io/)
- [SonarQube Documentation](https://docs.sonarqube.org/)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [Gitleaks Documentation](https://gitleaks.io/)
- [DefectDojo Documentation](https://docs.defectdojo.com/)
- [uFawkesObs — Observability Plane](https://github.com/paruff/uFawkesObs)

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## 📄 License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

## 🙋 Support

- GitHub Issues: https://github.com/paruff/uFawkesPipe/issues
- Documentation: https://github.com/paruff/uFawkesPipe/wiki

---

Built for platform engineers and developers

## uFawkes Stack Ecosystem

uFawkesPipe is part of the [uFawkes](https://ufawkes.dev) platform engineering ecosystem:

| Stack           | Description                                          | Link                                            |
| --------------- | ---------------------------------------------------- | ----------------------------------------------- |
| **uFawkesRes**  | Resource plane — PostgreSQL, Valkey, Traefik, Authelia | [GitHub](https://github.com/paruff/uFawkesRes)  |
| **uFawkesPipe** | CI/CD — Woodpecker, Buildpacks, DevSecOps            | [GitHub](https://github.com/paruff/uFawkesPipe) |
| **uFawkesObs**  | Observability — Prometheus, Grafana, Loki, OTEL      | [GitHub](https://github.com/paruff/uFawkesObs)  |
| **uFawkesDORA** | DORA metrics — dashboards, VSM, delivery performance | [GitHub](https://github.com/paruff/uFawkesDORA) |
| **uFawkesSec**  | Security — merged into uFawkesPipe (DefectDojo, Infisical, Trivy, Falco) | _merged_ |
| **uFawkesDevX** | Developer experience — golden paths, IDP templates   | [GitHub](https://github.com/paruff/uFawkesDevX) |
| **uFawkesAI**   | AI agent templates — golden path scaffolding         | [GitHub](https://github.com/paruff/uFawkesAI)   |

**Product Suite Roadmap**: [fawkes/ROADMAP.md](https://github.com/paruff/fawkes/blob/main/ROADMAP.md)
