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

Defines your application's identity. This section is **required**, but only `app.language` is enforced: the generator fails without it and reads no other `app` field.

| Field    | Type   | Required | Default | Description |
|----------|--------|----------|---------|-------------|
| `name`   | string | no       | —       | Application name. Used for image names, SonarQube project keys, and Kubernetes resources. |
| `type`   | string | no       | `service` | Application type. Valid values: `service`, `library`, `cli`, `frontend` |
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

Defines how your application is built into a container image. No `build` field is enforced.

| Field      | Type   | Required | Default  | Description |
|------------|--------|----------|----------|-------------|
| `builder`  | string | no       | `cnb`    | Build method. Valid values: `cnb` (Cloud Native Buildpacks), `docker` (Dockerfile), `custom` (custom script) |
| `cnb`      | object | no       | —        | CNB-specific configuration (see below) |
| `docker`   | object | no       | —        | Docker-specific configuration (see below) |
| `image`    | object | no       | —        | Image registry, name, and tag configuration (see below) |

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

**What the generated `build` step does:** it runs `pack build --publish` in the pinned `buildpacksio/pack` `-base` image (the default image has no shell, which Woodpecker needs) and pushes `<registry_username>/<repo name>:<first 7 characters of the commit SHA>` (or `build.image.namespace/name` when both are set) to Docker Hub. It needs the `registry_username` and `registry_password` Woodpecker secrets, which must be allowed for the `push` and `manual` events, because the step only runs for `push` and `manual` pipelines on `main`. Because the build already published the image, no separate `push` step is generated for `builder: cnb`, and `image_scan` scans that published tag. `pack` runs the builder in a container, so the step mounts the host Docker socket (`/var/run/docker.sock`). That is root-equivalent on the agent, and Woodpecker only allows it when the repo is trusted: set **Settings, Trusted, Volumes** on the repo in Woodpecker. Other registries than Docker Hub are not supported yet. `cnb.buildpacks` and `cnb.env` are accepted but not passed to `pack` yet.

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
| `namespace` | string | no       | —              | Registry namespace/organization (e.g., DockerHub username). Used with `name`: both set gives `namespace/name`, otherwise the image is `$CI_REPO_NAME`. |
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

Static Application Security Testing — SonarQube analysis, Bandit (Python), Trivy filesystem scanning.

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
| `bandit.enabled`      | boolean | no       | `true`  | Enable Bandit Python security linting |
| `bandit.severity`     | string  | no       | `MEDIUM` | Severity filter (LOW, MEDIUM, HIGH) |
| `bandit.confidence`   | string  | no       | `MEDIUM` | Confidence filter (LOW, MEDIUM, HIGH) |

**Setup (once per app repo).** The `sast` step reads two Woodpecker secrets:

1. In SonarQube, create a project whose key is `sonarqube.projectKey` (default `app.name`) and generate a token (My Account → Security).
2. In Woodpecker, add repo secrets `sonarqube_url` (e.g. `http://sonarqube:9000`) and `sonarqube_token`:
   `woodpecker-cli repo secret add --repository <owner>/<repo> --name sonarqube_token --value <token>`.

The quality-gate wait polls `/api/qualitygates/project_status` up to 60 times (5 s apart) and fails the step if the gate is not `OK` by then. Tracing uses `$CI_WORKSPACE/scripts/otel-trace.sh` when present and is skipped otherwise.

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
    bandit:
      enabled: true
      severity: MEDIUM
      confidence: MEDIUM
```

### dependency_scan

Scans application dependencies for known vulnerabilities.

| Field         | Type    | Required | Default     | Description |
|---------------|---------|----------|-------------|-------------|
| `enabled`     | boolean | no       | `true`      | Enable dependency scanning stage |
| `tools`       | array   | no       | `[trivy]`   | Scanning tool to use — exactly one, not a combinable set (see note) |
| `licenses`    | array   | no       | —           | Only with `tools: [osv-scanner]`: license allowlist passed to `--licenses` |

**Valid `tools` values:** `[trivy]` (default) or `[osv-scanner]`. `owasp-dependency-check` and `fail_on`/`suppressions` are documented elsewhere in this repo's history but are **not implemented** by `scripts/generate_woodpecker_yml.py` — see `docs/KNOWN_LIMITATIONS.md`. `tools` selects one tool per stage; combining multiple tools in a single `dependency_scan` stage is not supported.

**Example (default — Trivy):**

```yaml
stages:
  dependency_scan:
    enabled: true
```

**Example (OSV-Scanner — CVEs + license allowlist, P3-10):**

```yaml
stages:
  dependency_scan:
    enabled: true
    tools:
      - osv-scanner
    licenses:
      - MIT
      - Apache-2.0
```

Both tools write a machine-readable report to `artifacts/security/` (`trivy-repo.json` or `osv.json`) that the [`defectdojo`](#defectdojo) stage picks up if enabled.

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

### dast

Dynamic Application Security Testing — OWASP ZAP active scanning against running application.

| Field         | Type    | Required | Default         | Description |
|---------------|---------|----------|-----------------|-------------|
| `enabled`     | boolean | no       | `false`         | Enable DAST stage |
| `tool`        | string  | no       | `zap`           | DAST tool to use |
| `target_url`  | string  | yes      | —               | URL of running application (e.g., `http://app:8000`) |
| `openapi_url` | string  | no       | —               | OpenAPI spec URL; when set, `zap-api-scan.py` also runs. Unset = baseline scan only |
| `rules`       | array   | no       | `Default Policy` | ZAP policy/rules to run |
| `fail_on`     | string  | no       | `HIGH`          | Severity threshold to fail (HIGH, MEDIUM, LOW) |
| `timeout`     | integer | no       | `300`           | Max scan time in seconds |

**Valid tools:** `zap`

**Example:**

```yaml
stages:
  dast:
    enabled: true
    tool: zap
    target_url: http://my-app:8000
    rules: "Default Policy"
    fail_on: HIGH
    timeout: 300
```

**Migration (#289):** the API scan used to run by default against `<target_url>/openapi.json`. It now runs only when `openapi_url` is set; add `openapi_url: <target_url>/openapi.json` to keep the old behaviour.

**Note:** DAST requires the application to be running and accessible. Typically runs in a staging/integration environment after deployment.

---

### defectdojo

Uploads whatever machine-readable security reports the earlier stages produced (Trivy, Bandit, ZAP, OSV-Scanner) to a [DefectDojo](https://www.defectdojo.org/) instance for centralized findings tracking (P2-1, P3-8, P3-9).

| Field             | Type    | Required | Default                    | Description |
|-------------------|---------|----------|-----------------------------|-------------|
| `enabled`         | boolean | no       | `false`                     | Enable DefectDojo upload stage |
| `url`             | string  | no       | `http://defectdojo:8080`   | DefectDojo base URL |
| `engagement_name` | string  | no       | `CI-Engagement`             | Engagement to import findings into |

Requires a Woodpecker secret named `defectdojo_api_token`.

Each report is uploaded independently as `[ -f <report> ] && curl ... || true` — a report a given pipeline never produced (e.g. `dast` disabled, so no `zap-*.xml`) is silently skipped, and a failed upload never fails the build. Only runs on `push` to `main`.

**Example:**

```yaml
stages:
  defectdojo:
    enabled: true
    url: http://defectdojo:8080
    engagement_name: CI-Engagement
```

| Report | Produced by | DefectDojo `scan_type` |
|---|---|---|
| `artifacts/security/trivy-repo.json` | `dependency_scan` (tools: trivy) | `Trivy Scan` |
| `artifacts/security/trivy-image.json` | `image_scan` | `Trivy Scan` |
| `artifacts/security/bandit.json` | `sast` (bandit.enabled) | `Bandit Scan` |
| `artifacts/security/zap-baseline.xml` | `dast` | `ZAP Scan` |
| `artifacts/security/zap-api.xml` | `dast` | `ZAP Scan` |
| `artifacts/security/osv.json` | `dependency_scan` (tools: osv-scanner) | `OSV Scan` |

**Known limitation:** `OSV Scan` is DefectDojo's documented parser name as of this writing but has not been confirmed against a live DefectDojo instance from this repo — no `defectdojo` service was running in this environment during implementation. Confirm the parser name before the first real import.

---

### push

Pushes the built image to configured registries. With `builder: cnb` no `push` step is generated, because `pack build --publish` has already pushed the image; the stage applies to `builder: docker`.

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

### deploy

Deploys the built image to a target environment (Docker, Docker Compose, or remote host).

| Field           | Type    | Required | Default              | Description |
|-----------------|---------|----------|----------------------|-------------|
| `enabled`       | boolean | no       | `false`              | Enable deploy stage |
| `target`        | string  | no       | `docker`             | Deployment target: `docker`, `compose`, `ssh` |
| `host`          | string  | no       | `localhost`          | Target host (for `ssh` target) |
| `port`          | integer | no       | `22`                 | SSH port (for `ssh` target) |
| `user`          | string  | no       | `root`               | SSH user (for `ssh` target) |
| `ssh_key`       | string  | no       | —                    | Path to SSH private key (for `ssh` target) |
| `compose_file`  | string  | no       | `docker-compose.yml` | Compose file path (for `compose` target) |
| `service_name`  | string  | no       | `app.name`           | Service name in compose file |
| `port`          | integer | no       | `8000`               | Host port to expose |
| `network`       | string  | no       | `ufawkespipe_default`| Docker network to attach to |
| `env_file`      | string  | no       | —                    | Path to env file for container |

**Valid targets:** `docker`, `compose`, `ssh`

**Example (Docker):**

```yaml
stages:
  deploy:
    enabled: true
    target: docker
    port: 8080
    network: ufawkespipe_default
```

**Example (Docker Compose):**

```yaml
stages:
  deploy:
    enabled: true
    target: compose
    compose_file: docker-compose.prod.yml
    service_name: my-app
```

**Example (SSH):**

```yaml
stages:
  deploy:
    enabled: true
    target: ssh
    host: prod.example.com
    user: deploy
    ssh_key: /secrets/deploy_key
```

### notify_obs

Sends a `deployment` event to uFawkesObs's DORA ingestion API (`POST <dora_ingestion_url>/event`, see [dora-contract.md](dora-contract.md)), so the run counts in Deployment Frequency and Change Failure Rate. Optional; off by default. Runs last, only on `push` or `manual` pipelines on `main`, and also after a failed pipeline (sent as `status: failed`). The step never fails the pipeline, but it shows as failed when Obs doesn't answer `201`.

| Field     | Type    | Required | Default | Description |
|-----------|---------|----------|---------|-------------|
| `enabled` | boolean | no       | `false` | Enable the `notify-obs` step |
| `api_key` | boolean | no       | `false` | Also send the `dora_api_key` secret as a bearer token. Leave `false` when Obs has no auth: Woodpecker refuses to run a pipeline that references a secret which doesn't exist |

It reads the `dora_ingestion_url` Woodpecker secret (required, e.g. `http://dora-api:8088`) and, with `api_key: true`, the `dora_api_key` secret. The event has no `first_commit_at` or `pr_merged_at`, so lead time isn't computed for apps that use this generated step.

```yaml
stages:
  notify_obs:
    enabled: true
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
| `timeout`            | integer | no       | `60`    | Pipeline timeout in minutes. Written to the generated file as a comment only; Woodpecker CE has no per-pipeline YAML timeout (L-005). |

**Example:**

```yaml
advanced:
  timeout: 60
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
