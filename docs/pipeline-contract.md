# Pipeline Contract Reference — .fawkespipe.yml

**Version:** 1.0.0

The `.fawkespipe.yml` file defines the contract between your application repository and the uFawkesPipe CI/CD platform. Place this file at the root of your application repository to configure how your application is built, tested, scanned, and deployed.

> **Quick start:** Copy [`.fawkespipe.yml.example`](../.fawkespipe.yml.example) and customize it for your application.

---

## Table of Contents

- [Overview](#overview)
- [How Your Pipeline Gets Generated](#how-your-pipeline-gets-generated)
- [app — Application Metadata](#app--application-metadata)
- [build — Build Configuration](#build--build-configuration)
  - [CNB Builder](#cnb-builder)
  - [Docker Builder](#docker-builder)
  - [Image Configuration](#image-configuration)
- [stages — Pipeline Stages](#stages--pipeline-stages)
  - [lint](#lint)
  - [test](#test)
  - [sast](#sast)
  - [dependency_scan](#dependency_scan)
  - [build](#build-stage)
  - [image_scan](#image_scan)
  - [push](#push)
- [notifications — Notifications](#notifications--notifications)
- [kubernetes — Kubernetes Deployment](#kubernetes--kubernetes-deployment)
- [advanced — Advanced Configuration](#advanced--advanced-configuration)
- [Complete Example](#complete-example)
- [Language-Specific Examples](#language-specific-examples)

---

## Overview

A `.fawkespipe.yml` file has the following top-level structure:

```yaml
app:
  name: my-application
  type: service
  language: java
  version: 1.0.0

build:
  builder: cnb
  ...

stages:
  lint:
    enabled: true
  ...

notifications:
  ...

kubernetes:
  ...

advanced:
  ...
```

---

## How Your Pipeline Gets Generated

`.fawkespipe.yml` is not read by Woodpecker directly — Woodpecker only ever
executes a `.woodpecker.yml` file. `scripts/generate_woodpecker_yml.py`
translates your `.fawkespipe.yml` into that `.woodpecker.yml`:

```bash
# After creating or editing .fawkespipe.yml, generate/update .woodpecker.yml
make generate-pipeline

# In your app repo's own CI, gate on drift between the two files
make check-pipeline
```

`stages.*.enabled: false` removes that step from the generated pipeline
entirely (not a no-op skip); `app.language` selects the matching
`stages.<name>.commands` entry; `build.builder` (`cnb` or `docker`) selects
the build step body. See
[`examples/fawkespipe-contract-migration/`](../examples/fawkespipe-contract-migration/)
for a worked `.fawkespipe.yml` → `.woodpecker.yml` pair.

`kubernetes:` and `notifications:` are validated but do not yet produce
pipeline steps — see `docs/KNOWN_LIMITATIONS.md` L-005.

---

## app — Application Metadata

Defines your application's identity. This section is **required**.

| Field    | Type   | Required | Default | Description |
|----------|--------|----------|---------|-------------|
| `name`   | string | yes      | —       | Application name. Used for image names, SonarQube project keys, and Kubernetes resources. |
| `type`   | string | yes      | `service` | Application type. Valid values: `service`, `library`, `cli`, `frontend` |
| `language` | string | yes    | —       | Primary programming language. Valid values: `java`, `python`, `nodejs`, `go`, `ruby`, `php`, `dotnet`, `rust` |
| `version` | string | no       | auto-detected | Semantic version. Can be auto-generated from Git tags or CI variables. |

**Example:**

```yaml
app:
  name: my-app
  type: service
  language: python
  version: 1.0.0
```

---

## build — Build Configuration

Defines how your application is built into a container image. **Required**.

| Field      | Type   | Required | Default  | Description |
|------------|--------|----------|----------|-------------|
| `builder`  | string | yes      | `cnb`    | Build method. Valid values: `cnb` (Cloud Native Buildpacks), `docker` (Dockerfile), `custom` (custom script) |
| `cnb`      | object | no       | —        | CNB-specific configuration (see below) |
| `docker`   | object | no       | —        | Docker-specific configuration (see below) |
| `image`    | object | yes      | —        | Image registry, name, and tag configuration (see below) |

### CNB Builder

Used when `builder: cnb`. Builds OCI-compliant container images using Cloud Native Buildpacks without a Dockerfile.

| Field        | Type   | Required | Default                           | Description |
|--------------|--------|----------|-----------------------------------|-------------|
| `builder`    | string | no       | `paketobuildpacks/builder:base`   | CNB builder image. Determines the available buildpacks and base OS. |
| `buildpacks` | array  | no       | `[]`                              | Specific buildpacks to use. Empty = auto-detect from source code. |
| `env`        | object | no       | `{}`                              | Build-time environment variables (e.g., `BP_JVM_VERSION`, `BP_MAVEN_BUILD_ARGUMENTS`). |

**Example:**

```yaml
build:
  builder: cnb
  cnb:
    builder: paketobuildpacks/builder:base
    buildpacks: []
    env:
      BP_JVM_VERSION: "17"
      BP_MAVEN_BUILD_ARGUMENTS: "-DskipTests"
```

**Common CNB environment variables:**

| Variable                    | Description |
|-----------------------------|-------------|
| `BP_JVM_VERSION`            | JVM version for Java buildpacks |
| `BP_MAVEN_BUILD_ARGUMENTS`  | Maven build arguments |
| `BP_GRADLE_BUILD_ARGUMENTS` | Gradle build arguments |
| `BP_NODE_VERSION`           | Node.js version |
| `BP_PYTHON_VERSION`         | Python version |
| `BP_GO_VERSION`             | Go version |
| `BP_RUBY_VERSION`           | Ruby version |

### Docker Builder

Used when `builder: docker`. Builds images using a Dockerfile.

| Field        | Type   | Required | Default        | Description |
|--------------|--------|----------|----------------|-------------|
| `dockerfile` | string | no       | `Dockerfile`   | Path to Dockerfile |
| `context`    | string | no       | `.`            | Docker build context directory |
| `target`     | string | no       | —              | Multi-stage build target stage |
| `buildArgs`  | object | no       | `{}`           | Docker build arguments (`--build-arg`) |

**Example:**

```yaml
build:
  builder: docker
  docker:
    dockerfile: Dockerfile
    context: .
    target: production
    buildArgs:
      APP_VERSION: "${APP_VERSION}"
```

### Image Configuration

Configures the container image name, registry, and tag strategy.

| Field       | Type   | Required | Default        | Description |
|-------------|--------|----------|----------------|-------------|
| `registry`  | string | no       | `docker.io`    | Container registry hostname |
| `namespace` | string | yes      | —              | Registry namespace/organization (e.g., DockerHub username) |
| `name`      | string | no       | `app.name`     | Image name. Defaults to the app name. |
| `tags`      | array  | no       | `[short-sha]`  | List of tags to apply. Supports CI variable interpolation. |

**Tag variables:**

| Variable             | Description |
|----------------------|-------------|
| `${GIT_COMMIT_SHORT}` | Short Git commit SHA (7 characters) |
| `${GIT_BRANCH}`       | Git branch name (sanitized) |
| `${GIT_TAG}`          | Git tag (if available) |
| `${CI_PIPELINE_NUMBER}` | CI pipeline number |

**Example:**

```yaml
build:
  builder: cnb
  image:
    registry: docker.io
    namespace: ${DOCKERHUB_USERNAME}
    name: ${APP_NAME}
    tags:
      - "${GIT_COMMIT_SHORT}"
      - "${GIT_BRANCH}"
      - "latest"
```

---

## stages — Pipeline Stages

Configures which pipeline stages are enabled and their behavior. All stages are optional — set `enabled: false` to skip.

### lint

Code quality and style checks.

| Field       | Type    | Required | Default | Description |
|-------------|---------|----------|---------|-------------|
| `enabled`   | boolean | no       | `true`  | Enable lint stage |
| `commands`  | array   | no       | —       | Language-specific lint commands (see below) |
| `dockerfile.enabled` | boolean | no | `true`  | Enable Dockerfile linting with hadolint |

**Commands array** defines language-specific lint commands:

```yaml
commands:
  - language: java
    cmd: mvn checkstyle:check spotbugs:check
  - language: python
    cmd: pylint src/ && black --check src/
  - language: nodejs
    cmd: npm run lint
  - language: go
    cmd: golangci-lint run
```

**Example:**

```yaml
stages:
  lint:
    enabled: true
    commands:
      - language: python
        cmd: ruff check src/ && ruff format --check src/
    dockerfile:
      enabled: true
```

### test

Unit and integration tests with optional coverage thresholds.

| Field              | Type    | Required | Default | Description |
|--------------------|---------|----------|---------|-------------|
| `enabled`          | boolean | no       | `true`  | Enable test stage |
| `commands`         | array   | no       | —       | Language-specific test commands (same format as lint) |
| `coverage.enabled` | boolean | no       | `true`  | Enable coverage collection |
| `coverage.threshold` | integer | no     | `80`    | Minimum coverage percentage |
| `coverage.report`  | string  | no       | `coverage.xml` | Coverage report file path |

**Commands by language:**

| Language | Command |
|----------|---------|
| java     | `mvn test` |
| python   | `pytest tests/ --cov=src --cov-report=xml` |
| nodejs   | `npm test -- --coverage` |
| go       | `go test -v -cover ./...` |

**Example:**

```yaml
stages:
  test:
    enabled: true
    commands:
      - language: python
        cmd: pytest tests/ --cov=src --cov-report=xml
    coverage:
      enabled: true
      threshold: 80
      report: coverage.xml
```

### sast

Static Application Security Testing — SonarQube analysis and optional Trivy filesystem scanning.

| Field                 | Type    | Required | Default | Description |
|-----------------------|---------|----------|---------|-------------|
| `enabled`             | boolean | no       | `true`  | Enable SAST stage |
| `sonarqube.enabled`   | boolean | no       | `true`  | Enable SonarQube analysis |
| `sonarqube.projectKey` | string | no       | `app.name` | SonarQube project key |
| `sonarqube.sources`   | string  | no       | `src/`  | Source directories to analyze |
| `sonarqube.exclusions` | string | no       | `**/test/**,**/tests/**` | File exclusions pattern |
| `sonarqube.qualityGate` | boolean | no     | `true`  | Wait for quality gate result |
| `trivy.enabled`       | boolean | no       | `true`  | Enable Trivy filesystem scan |
| `trivy.severity`      | string  | no       | `HIGH,CRITICAL` | Severity filter for findings |

**Example:**

```yaml
stages:
  sast:
    enabled: true
    sonarqube:
      enabled: true
      projectKey: my-app
      sources: src/
      exclusions: "**/test/**,**/tests/**"
      qualityGate: true
    trivy:
      enabled: true
      severity: HIGH,CRITICAL
```

### dependency_scan

Scans application dependencies for known vulnerabilities.

| Field         | Type    | Required | Default                              | Description |
|---------------|---------|----------|--------------------------------------|-------------|
| `enabled`     | boolean | no       | `true`                               | Enable dependency scanning stage |
| `tools`       | array   | no       | `[owasp-dependency-check, trivy]`    | Scanning tools to use |
| `fail_on`     | string  | no       | `CRITICAL`                           | Severity threshold to fail the build |
| `suppressions` | string | no       | —                                     | Path to OWASP Dependency-Check suppressions XML |

**Valid tools:** `owasp-dependency-check`, `trivy`

**Valid fail_on values:** `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`

**Example:**

```yaml
stages:
  dependency_scan:
    enabled: true
    tools:
      - owasp-dependency-check
      - trivy
    fail_on: CRITICAL
    suppressions: dependency-check-suppressions.xml
```

### build (stage)

Controls whether the build stage executes. Build behavior is configured in the top-level [`build`](#build--build-configuration) section.

| Field     | Type    | Required | Default | Description |
|-----------|---------|----------|---------|-------------|
| `enabled` | boolean | no       | `true`  | Enable container image build |

```yaml
stages:
  build:
    enabled: true
```

### image_scan

Scans the built container image for vulnerabilities.

| Field       | Type    | Required | Default           | Description |
|-------------|---------|----------|-------------------|-------------|
| `enabled`   | boolean | no       | `true`            | Enable image scanning stage |
| `tools`     | array   | no       | `[trivy]`         | Scanning tools to use |
| `severity`  | string  | no       | `HIGH,CRITICAL`   | Severity filter |
| `fail_on`   | string  | no       | `CRITICAL`        | Severity threshold to fail the build |

**Example:**

```yaml
stages:
  image_scan:
    enabled: true
    tools:
      - trivy
    severity: HIGH,CRITICAL
    fail_on: CRITICAL
```

### push

Pushes the built image to configured registries.

| Field        | Type    | Required | Default      | Description |
|--------------|---------|----------|--------------|-------------|
| `enabled`    | boolean | no       | `true`       | Enable image push stage |
| `registries` | array   | no       | `[docker.io]` | Registries to push to |

**Example:**

```yaml
stages:
  push:
    enabled: true
    registries:
      - docker.io
      - ghcr.io
```

---

## notifications — Notifications

Configure pipeline event notifications.

### Slack

| Field         | Type    | Required | Default  | Description |
|---------------|---------|----------|----------|-------------|
| `enabled`     | boolean | no       | `false`  | Enable Slack notifications |
| `channel`     | string  | yes      | —        | Slack channel to post to |
| `events`      | array   | no       | —        | Events that trigger notifications |

**Valid events:** `build_success`, `build_failure`, `deployment`

**Example:**

```yaml
notifications:
  slack:
    enabled: true
    channel: "#ci-cd"
    events:
      - build_success
      - build_failure
      - deployment
```

### Email

| Field        | Type    | Required | Default  | Description |
|--------------|---------|----------|----------|-------------|
| `enabled`    | boolean | no       | `false`  | Enable email notifications |
| `recipients` | array   | yes      | —        | Email addresses to notify |

**Example:**

```yaml
notifications:
  email:
    enabled: false
    recipients:
      - dev-team@example.com
    events:
      - build_failure
```

---

## kubernetes — Kubernetes Deployment

Configuration for deploying to Kubernetes (promotion path from Docker Compose).

| Field                | Type    | Required | Default   | Description |
|----------------------|---------|----------|-----------|-------------|
| `enabled`            | boolean | no       | `false`   | Enable K8s deployment |
| `cluster`            | string  | no       | `default` | K8s cluster context name |
| `namespace`          | string  | no       | `default` | K8s namespace |
| `manifests.path`     | string  | no       | `k8s/`    | Directory containing K8s manifests |
| `manifests.files`    | array   | no       | —         | Specific manifest files to apply |
| `helm.enabled`       | boolean | no       | `false`   | Use Helm for deployment |
| `helm.chart`         | string  | no       | —         | Helm chart path |
| `helm.values`        | string  | no       | —         | Helm values file |
| `helm.release`       | string  | no       | `app.name` | Helm release name |

**Example (manifest-based):**

```yaml
kubernetes:
  enabled: true
  cluster: production
  namespace: my-app
  manifests:
    path: k8s/
    files:
      - deployment.yaml
      - service.yaml
```

**Example (Helm-based):**

```yaml
kubernetes:
  enabled: true
  helm:
    enabled: true
    chart: ./helm/my-app
    values: values.yaml
    release: my-app
```

---

## advanced — Advanced Configuration

Fine-tune pipeline behavior.

| Field                | Type    | Required | Default | Description |
|----------------------|---------|----------|---------|-------------|
| `timeout`            | integer | no       | `60`    | Pipeline timeout in minutes |
| `retry.enabled`      | boolean | no       | `true`  | Enable automatic retry on failure |
| `retry.count`        | integer | no       | `2`     | Maximum retry attempts |
| `parallel.enabled`   | boolean | no       | `false` | Run independent stages in parallel |
| `artifacts.paths`    | array   | no       | —       | Paths to archive as build artifacts |
| `artifacts.retention` | integer | no      | `30`    | Days to retain artifacts |
| `workspace.cleanup`  | boolean | no       | `true`  | Clean workspace after build |

**Example:**

```yaml
advanced:
  timeout: 60
  retry:
    enabled: true
    count: 2
  parallel:
    enabled: false
  artifacts:
    paths:
      - target/*.jar
      - dist/
      - build/
    retention: 30
  workspace:
    cleanup: true
```

---

## Complete Example

Here is a complete `.fawkespipe.yml` for a Java application using Cloud Native Buildpacks:

```yaml
# uFawkesPipe Pipeline Contract — v1.0.0
app:
  name: my-application
  type: service
  language: java
  version: 1.0.0

build:
  builder: cnb
  cnb:
    builder: paketobuildpacks/builder:base
    buildpacks: []
    env:
      BP_JVM_VERSION: "17"
  image:
    registry: docker.io
    namespace: ${DOCKERHUB_USERNAME}
    name: ${APP_NAME}
    tags:
      - "${GIT_COMMIT_SHORT}"
      - "${GIT_BRANCH}"
      - "latest"

stages:
  lint:
    enabled: true
    commands:
      - language: java
        cmd: mvn checkstyle:check spotbugs:check
    dockerfile:
      enabled: true

  test:
    enabled: true
    commands:
      - language: java
        cmd: mvn test
    coverage:
      enabled: true
      threshold: 80
      report: coverage.xml

  sast:
    enabled: true
    sonarqube:
      enabled: true
      projectKey: ${APP_NAME}
      sources: src/
      exclusions: "**/test/**,**/tests/**"
      qualityGate: true
    trivy:
      enabled: true
      severity: HIGH,CRITICAL

  dependency_scan:
    enabled: true
    tools:
      - owasp-dependency-check
      - trivy
    fail_on: CRITICAL
    suppressions: dependency-check-suppressions.xml

  build:
    enabled: true

  image_scan:
    enabled: true
    tools:
      - trivy
    severity: HIGH,CRITICAL
    fail_on: CRITICAL

  push:
    enabled: true
    registries:
      - docker.io

notifications:
  slack:
    enabled: false
    channel: "#ci-cd"
    events:
      - build_success
      - build_failure
      - deployment

kubernetes:
  enabled: false
  cluster: default
  namespace: default

advanced:
  timeout: 60
  retry:
    enabled: true
    count: 2
  artifacts:
    paths:
      - target/*.jar
    retention: 30
  workspace:
    cleanup: true
```

---

## Language-Specific Examples

Ready-to-use `.fawkespipe.yml` files for different application stacks:

| Language   | Example File |
|------------|-------------|
| Java/Maven | [examples/.fawkespipe-java-maven.yml](../examples/.fawkespipe-java-maven.yml) |
| Python/Flask | [examples/.fawkespipe-python-flask.yml](../examples/.fawkespipe-python-flask.yml) |
| Node.js/Express | [examples/.fawkespipe-nodejs-express.yml](../examples/.fawkespipe-nodejs-express.yml) |
| Go | [examples/.fawkespipe-go.yml](../examples/.fawkespipe-go.yml) |

---

> See the reference [`.fawkespipe.yml.example`](../.fawkespipe.yml.example) for the canonical template with inline documentation.
