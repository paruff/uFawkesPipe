# uFawkesPipe

[![CI](https://github.com/paruff/uFawkesPipe/actions/workflows/ci.yml/badge.svg)](https://github.com/paruff/uFawkesPipe/actions/workflows/ci.yml) [![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

**Integration & Delivery Plane of the Fawkes IDP Family**

uFawkesPipe is a production-ready CI/CD platform built on Jenkins, designed for polyglot application development with a standardized pipeline contract. It provides automated build, test, security scanning, and deployment capabilities using Cloud Native Buildpacks and modern DevSecOps practices.

## 🚀 Features

- **Polyglot Support** - Build applications in Java, Python, Node.js, Go, Ruby, and more
- **Standard Pipeline Contract** - Define CI/CD behavior via `.fawkespipe.yml` configuration
- **Cloud Native Buildpacks** - Build OCI-compliant container images without Dockerfiles
- **Security First** - Integrated SAST, dependency scanning, and container image scanning
- **Jenkins-based** - Robust, battle-tested CI/CD orchestration
- **Webhook APIs** - External planes can trigger pipelines via REST APIs
- **K8s Ready** - Clear promotion path to Kubernetes production environments
- **Single-node Dev** - Full stack runs on docker-compose for local development

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
│  │   Jenkins    │  │  SonarQube   │  │  Dependency  │      │
│  │   Master     │  │   (SAST)     │  │    Check     │      │
│  │              │  │              │  │              │      │
│  │  - Webhooks  │  │  - Quality   │  │  - OWASP DC  │      │
│  │  - Pipelines │  │    Gates     │  │  - Trivy     │      │
│  │  - JCasC     │  │  - Coverage  │  │              │      │
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
│                  │   DockerHub     │                         │
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
   # Edit .env with your credentials
   nano .env
   ```

   **Required configuration:**

   - `DOCKERHUB_USERNAME` - Your DockerHub username
   - `DOCKERHUB_TOKEN` - DockerHub access token or password
   - `JENKINS_ADMIN_PASSWORD` - Change default admin password

3. **Start the platform**

   ```bash
   docker-compose up -d
   ```

4. **Wait for services to start** (2-3 minutes)

   ```bash
   docker-compose logs -f jenkins
   # Wait for "Jenkins is fully up and running"
   ```

5. **Access the platform**
   - **Jenkins**: http://localhost:8080/jenkins
     - Username: `admin`
     - Password: (from `.env` file)
   - **SonarQube**: http://localhost:9000
     - Username: `admin`
     - Password: `admin` (change on first login) # pragma: allowlist secret

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

2. **Copy the standard Jenkinsfile to your repo**

   ```bash
    cp /path/to/uFawkesPipe/Jenkinsfile /path/to/your/repo/
   ```

3. **Create a pipeline job in Jenkins**
   - Go to Jenkins → New Item
   - Choose "Pipeline"
   - Configure Git repository URL
   - Set Script Path to `Jenkinsfile`
   - Save and run!

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

uFawkesPipe exposes Jenkins webhook APIs for external plane integration.

### Trigger Pipeline via Webhook

**Generic Webhook Trigger** (recommended for external systems):

```bash
curl -X POST "http://localhost:8080/jenkins/generic-webhook-trigger/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/user/repo",
    "branch": "main",
    "webhook_secret": "your-secret" # pragma: allowlist secret
  }'
```

**GitHub Webhook Integration**:

Configure in GitHub: Settings → Webhooks → Add webhook

- Payload URL: `http://your-jenkins:8080/jenkins/github-webhook/`
- Content type: `application/json`
- Events: Push, Pull Request

### REST API

Jenkins provides a full REST API:

```bash
# Get job info
curl -u admin:password "http://localhost:8080/jenkins/job/my-job/api/json"

# Trigger build with parameters
curl -X POST -u admin:password \
  "http://localhost:8080/jenkins/job/my-job/buildWithParameters?BRANCH=develop"

# Get build status
curl -u admin:password \
  "http://localhost:8080/jenkins/job/my-job/lastBuild/api/json"
```

## ☸️ Kubernetes Promotion Path

uFawkesPipe is designed for single-node development but provides a clear path to Kubernetes production.

### Development → Production Promotion

1. **Development** (Current): Docker Compose on single node
2. **Staging**: Kubernetes cluster with CI/CD namespace
3. **Production**: Kubernetes cluster with automated promotion

### Migration to Kubernetes

**Replace docker-compose services with K8s manifests:**

```yaml
# Jenkins on K8s
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: jenkins
spec:
  serviceName: jenkins
  replicas: 1
  template:
    spec:
      containers:
        - name: jenkins
          image: ufawkespipe/jenkins:latest
          volumeMounts:
            - name: jenkins-home
              mountPath: /var/jenkins_home
  volumeClaimTemplates:
    - metadata:
        name: jenkins-home
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 20Gi
```

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

### Jenkins Configuration as Code (JCasC)

Jenkins is configured via `jenkins/casc.yaml`. Modify this file to:

- Add users and permissions
- Configure external integrations
- Set up pipeline libraries
- Define global tool installations

### Service Configuration

Edit `docker-compose.yml` to:

- Change exposed ports
- Add more services (Nexus, Harbor, etc.)
- Configure resource limits
- Add additional networks

### Volume Management

Persistent data is stored in Docker volumes:

- `jenkins_home` - Jenkins data and jobs
- `sonarqube_data` - SonarQube analysis data
- `sonarqube_db` - PostgreSQL database
- `dependency_check_data` - CVE database cache
- `pack_cache` - CNB build cache

**Backup volumes:**

```bash
docker run --rm -v ufp_jenkins_home:/data -v $(pwd):/backup alpine \
  tar czf /backup/jenkins-backup.tar.gz -C /data .
```

## 🐛 Troubleshooting

### Jenkins won't start

```bash
# Check logs
docker-compose logs jenkins

# Increase memory
# Edit docker-compose.yml: JAVA_OPTS=-Xmx4g

# Reset Jenkins
docker-compose down
docker volume rm ufp_jenkins_home
docker-compose up -d
```

### SonarQube quality gate fails

```bash
# Check SonarQube logs
docker-compose logs sonarqube

# Access SonarQube UI to review quality gate rules
# http://localhost:9000
```

### Pack build fails

```bash
# Check Docker access
docker ps

# Verify builder image
docker pull paketobuildpacks/builder:base

# Check pack logs in Jenkins build console
```

### Dependency-Check is slow

- First run downloads CVE database (10-30 minutes)
- Subsequent runs use cached data (faster)
- Consider disabling for development builds

## 📚 Additional Resources

- [Jenkins Pipeline Documentation](https://www.jenkins.io/doc/book/pipeline/)
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
| **uFawkesPipe** | CI/CD — Jenkins, Buildpacks, DevSecOps               | [GitHub](https://github.com/paruff/ufawkespipe) |
| **uFawkesDORA** | DORA metrics — dashboards, VSM, delivery performance | [GitHub](https://github.com/paruff/ufawkesdora) |
| **uFawkesSec**  | Security — policy-as-code, supply chain, guardrails  | [GitHub](https://github.com/paruff/ufawkessec)  |
| **uFawkesDevX** | Developer experience — golden paths, IDP templates   | [GitHub](https://github.com/paruff/ufawkesdevx) |
| **uFawkesAI**   | AI agent templates — golden path scaffolding         | [GitHub](https://github.com/paruff/ufawkesai)   |

**Product Suite Roadmap**: [fawkes/ROADMAP.md](https://github.com/paruff/fawkes/blob/main/ROADMAP.md)
