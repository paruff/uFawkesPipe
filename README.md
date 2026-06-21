# uFawkesPipe

[![CI](https://github.com/paruff/uFawkesPipe/actions/workflows/ci.yml/badge.svg)](https://github.com/paruff/uFawkesPipe/actions/workflows/ci.yml) [![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

**Integration & Delivery Plane of the Fawkes IDP Family**

uFawkesPipe is a production-ready CI/CD platform built on Woodpecker CI and Portainer CD, designed for polyglot application development with a standardized pipeline contract. It provides automated build, test, security scanning, and deployment capabilities using Cloud Native Buildpacks and modern DevSecOps practices.

## 🚀 Features

- **Polyglot Support** - Build applications in Java, Python, Node.js, Go, Ruby, and more
- **Standard Pipeline Contract** - Define CI/CD behavior via `.fawkespipe.yml` configuration
- **Cloud Native Buildpacks** - Build OCI-compliant container images without Dockerfiles
- **Security First** - Integrated SAST, dependency scanning, and container image scanning
- **Woodpecker-based** - Lightweight, YAML-driven CI/CD orchestration
- **Webhook APIs** - External planes can trigger pipelines via REST APIs
- **K8s Ready** - Clear promotion path to Kubernetes production environments
- **Single-node Dev** - Full stack runs on Docker Compose for local development

## 📋 Pipeline Stages

Every pipeline in uFawkesPipe follows these standardized stages:

1. **Lint** - Code quality and style checks (language-specific)
2. **Unit Tests** - Automated testing with coverage reporting
3. **SAST** - Static Application Security Testing (SonarQube + Trivy)
4. **Dependency Scan** - Vulnerability scanning (OWASP Dependency-Check + Trivy)
5. **Build** - Container image build via Cloud Native Buildpacks or Docker
6. **Image Scan** - Container vulnerability scanning (Trivy)
7. **Push** - Push images to DockerHub (or other registries)
8. **Deploy** - Optional Kubernetes deployment

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    uFawkesPipe Platform                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Woodpecker  │  │  SonarQube   │  │  Portainer   │      │
│  │  CI          │  │   (SAST)     │  │   CE (CD)    │      │
│  │              │  │              │  │              │      │
│  │  - Pipelines │  │  - Quality   │  │  - Deploy    │      │
│  │  - Webhooks  │  │    Gates     │  │  - Stacks    │      │
│  │  - Secrets   │  │  - Coverage  │  │  - Volumes   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                           │                                  │
│                  ┌────────▼────────┐                         │
│                  │   CNB Builder   │                         │
│                  │   (Pack CLI)    │                         │
│                  └────────┬────────┘                         │
│                           │                                  │
│                           ▼                                  │
│                  ┌─────────────────┐                         │
│                  │   Docker        │                         │
│                  │   Registry      │                         │
│                  └─────────────────┘                         │
│                                                               │
└───────────────────────────────────────┬───────────────────────┘
                                        │
                                        │ Promotion Path
                                        ▼
                        ┌───────────────────────────┐
                        │   Kubernetes Cluster      │
                        │   (Production)            │
                        └───────────────────────────┘
```

## 🛠️ Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose v2.0+
- 4GB+ RAM available for containers
- DockerHub account (for image push)

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

   **Required configuration:**

   - `REGISTRY_USERNAME` - Your registry username
   - `REGISTRY_TOKEN` - DockerHub access token or password
   - `WOODPECKER_GITHUB_CLIENT` - GitHub OAuth client ID
   - `WOODPECKER_GITHUB_SECRET` - GitHub OAuth client secret
   - `WOODPECKER_AGENT_SECRET` - Shared secret between server and agent
   - `SONARQUBE_ADMIN_PASSWORD` - Change default SonarQube admin password

3. **Start the platform**

   ```bash
   make up
   ```

4. **Wait for services to start** (<30 seconds)

   ```bash
   make logs
   ```

5. **Access the platform**
   - **Woodpecker CI**: http://localhost:8000
     - Authenticate via GitHub OAuth
   - **Portainer CD**: https://localhost:9443
     - Create admin account on first login
   - **SonarQube**: http://localhost:9001
     - Username: `admin`
     - Password: (from `SONARQUBE_ADMIN_PASSWORD` in `.env`)

### First Pipeline

1. **Create a `.fawkespipe.yml` in your application repository**

   Example for a Node.js app:

   ```yaml
   app:
     name: my-app
     type: service
     language: nodejs

   build:
     builder: cnb
     image:
       namespace: myorg
       name: my-app

   stages:
     lint:
       enabled: true
       commands:
         - language: nodejs
           cmd: npm run lint

     test:
       enabled: true
       commands:
         - language: nodejs
           cmd: npm test

     sast:
       enabled: true

     dependency_scan:
       enabled: true

     push:
       enabled: true
   ```

2. **Create a `.woodpecker.yml` in your application repository**

   ```yaml
   pipeline:
     build:
       image: alpine:3.20
       commands:
         - echo "Building $(basename $(pwd))..."
   ```

3. **Add the pipeline to Woodpecker CI**
   - Go to Woodpecker CI → Repositories
   - Activate your repository
   - Woodpecker will automatically discover `.woodpecker.yml`
   - Push code to trigger the pipeline!

   See `.woodpecker.yml` for uFawkesPipe's own pipeline definition.

## 📖 Pipeline Contract Reference

The `.fawkespipe.yml` file defines how your application should be built and deployed. See [.fawkespipe.yml.example](./.fawkespipe.yml.example) for a complete reference.

### Key Sections

- **`app`** - Application metadata (name, type, language)
- **`build`** - Build configuration (CNB or Docker)
- **`stages`** - Enable/disable and configure pipeline stages
- **`notifications`** - Slack, email notifications
- **`kubernetes`** - Kubernetes deployment configuration

### Language-Specific Examples

- [Java/Maven](./examples/.fawkespipe-java-maven.yml)
- [Python/Flask](./examples/.fawkespipe-python-flask.yml)
- [Node.js/Express](./examples/.fawkespipe-nodejs-express.yml)
- [Go](./examples/.fawkespipe-go.yml)

## 🔌 Webhook API

uFawkesPipe exposes Woodpecker CI webhooks for external plane integration.

### Trigger Pipeline via Webhook

Woodpecker CI automatically receives push webhooks from GitHub when a repository is activated.

**GitHub Webhook Integration**:

Configure in GitHub: Settings → Webhooks → Add webhook

- Payload URL: `http://your-woodpecker:8000/api/hooks/<repository-id>`
- Content type: `application/json`
- Events: Push, Pull Request

### CLI Trigger

Trigger a pipeline from the command line using the Woodpecker CLI:

```bash
# Install Woodpecker CLI (if not already installed)
# See https://woodpecker-ci.org/docs/cli

# Trigger the latest pipeline
woodpecker-cli exec

# Trigger a specific pipeline
woodpecker-cli pipeline start <repository-id> <pipeline-number>
```

## ☸️ Kubernetes Promotion Path

uFawkesPipe is designed for single-node development but provides a clear path to Kubernetes production.

### Development → Production Promotion

1. **Development** (Current): Docker Compose on single node
2. **Staging**: Kubernetes cluster with CI/CD namespace
3. **Production**: Kubernetes cluster with automated promotion

### Migration to Kubernetes

**Deploy uFawkesPipe services on Kubernetes using the manifests in `k8s/`:**

See [`k8s/`](./k8s/) for example Kubernetes manifests for Woodpecker, Portainer, and SonarQube.

**Kubernetes Pipeline Integration:**

Enable in `.fawkespipe.yml`:

```yaml
kubernetes:
  enabled: true
  cluster: production
  namespace: my-app
  manifests:
    path: k8s/
```

### Helm Deployment

uFawkesPipe also supports Helm deployments:

```yaml
kubernetes:
  helm:
    enabled: true
    chart: ./helm/my-app
    release: my-app
    values: values.yaml
```

## 🔒 Security Features

### Static Application Security Testing (SAST)

- **SonarQube** - Code quality and security vulnerabilities
- **Trivy** - Filesystem and code scanning

### Dependency Scanning

- **OWASP Dependency-Check** - Known vulnerable dependencies (CVE database)
- **Trivy** - Comprehensive vulnerability database

### Container Scanning

- **Trivy** - Container image vulnerability scanning
- **Hadolint** - Dockerfile best practices

### Security Best Practices

- Fail builds on critical vulnerabilities
- Quality gates for code coverage and security
- Automated security scanning in every pipeline
- Container image signing (roadmap)

## 🔧 Configuration

### Pipeline Configuration

The pipeline is defined in `.woodpecker.yml`. Customize it to:

- Add or remove pipeline steps
- Configure Docker-in-Docker for container builds
- Set environment variables for different stages
- Define secrets for registry authentication

### Service Configuration

Edit `compose.yaml` to:

- Change exposed ports
- Add more services (Nexus, Harbor, etc.)
- Configure resource limits
- Add additional networks

### Volume Management

Persistent data is stored in Docker volumes:

- `woodpecker_data` - Woodpecker CI database and config
- `portainer_data` - Portainer CD data
- `sonarqube_data` - SonarQube analysis data
- `pack_cache` - CNB build cache

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

# Reset Woodpecker data
make down
docker volume rm ufp_woodpecker_data
make up
```

### SonarQube quality gate fails

```bash
# Check SonarQube logs
make logs sonarqube

# Access SonarQube UI to review quality gate rules
# http://localhost:9001
```

### Pack build fails

```bash
# Check Docker access
docker ps

# Verify builder image
docker pull paketobuildpacks/builder:base

# Check pack logs in Woodpecker CI build output
```

### Dependency-Check is slow

- First run downloads CVE database (10-30 minutes)
- Subsequent runs use cached data (faster)
- Consider disabling for development builds

## 📚 Additional Resources

- [Woodpecker CI Documentation](https://woodpecker-ci.org/docs/intro)
- [Cloud Native Buildpacks](https://buildpacks.io/)
- [SonarQube Documentation](https://docs.sonarqube.org/)
- [OWASP Dependency-Check](https://owasp.org/www-project-dependency-check/)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## 📄 License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## 🙋 Support

- GitHub Issues: https://github.com/paruff/uFawkesPipe/issues
- Documentation: https://github.com/paruff/uFawkesPipe/wiki

---

Built with ❤️ for platform engineers and developers

## uFawkes Stack Ecosystem

uFawkesPipe is part of the [uFawkes](https://ufawkes.dev) platform engineering ecosystem:

| Stack           | Description                                          | Link                                            |
| --------------- | ---------------------------------------------------- | ----------------------------------------------- |
| **uFawkesObs**  | Observability — Prometheus, Grafana, AI dashboards   | [GitHub](https://github.com/paruff/ufawkesobs)  |
| **uFawkesPipe** | CI/CD — Woodpecker, Buildpacks, DevSecOps            | [GitHub](https://github.com/paruff/ufawkespipe) |
| **uFawkesDORA** | DORA metrics — dashboards, VSM, delivery performance | [GitHub](https://github.com/paruff/ufawkesdora) |
| **uFawkesSec**  | Security — policy-as-code, supply chain, guardrails  | [GitHub](https://github.com/paruff/ufawkessec)  |
| **uFawkesDevX** | Developer experience — golden paths, IDP templates   | [GitHub](https://github.com/paruff/ufawkesdevx) |
| **uFawkesAI**   | AI agent templates — golden path scaffolding         | [GitHub](https://github.com/paruff/ufawkesai)   |

**Product Suite Roadmap**: [fawkes/ROADMAP.md](https://github.com/paruff/fawkes/blob/main/ROADMAP.md)
