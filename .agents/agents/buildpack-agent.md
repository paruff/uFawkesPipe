---
name: buildpack-agent
description: Cloud Native Buildpacks (CNB) and language pack specialist for uFawkesPipe. Primary build mechanism is CNB; Dockerfiles are generated via Score for deployment.
applies: pack/**/*, examples/**/*, docker-compose.yml
---

# Buildpack Agent

Specialist for creating language packs that define how different application stacks are built, tested, and scanned within uFawkesPipe using **Cloud Native Buildpacks (CNB)** as the primary build mechanism. **Dockerfiles are generated via Score** for deployment targets that require them (Docker, K8s).

## Context Files — Read First

| Priority | File                        | What You Learn                                   |
| -------- | --------------------------- | ------------------------------------------------ |
| 1        | `AGENTS.md`                 | PM contract, boundaries, rules                   |
| 2        | `pack/Dockerfile`           | Builder image configuration (not app Dockerfile) |
| 3        | `docker-compose.yml`        | pack-cli service configuration                   |
| 4        | `.fawkespipe.yml.example`   | How builders are configured in pipeline contract |
| 5        | `examples/`                 | Existing language examples                       |
| 6        | `.woodpecker.yml` (Build stage) | How pack CLI is invoked in pipeline          |

## Language Matrix

| Language | Builder                         | Build Env Vars            | Lint                | Test             | SAST              | Dep Scan       |
| -------- | ------------------------------- | ------------------------- | ------------------- | ---------------- | ----------------- | -------------- |
| Java     | `paketobuildpacks/builder:base` | `BP_JVM_VERSION=17`       | checkstyle          | mvn test         | SonarQube         | OWASP + Trivy  |
| Python   | `paketobuildpacks/builder:base` | `BP_CPYTHON_VERSION=3.11` | pylint/black/flake8 | pytest + cov     | Bandit            | Safety + Trivy |
| Node.js  | `paketobuildpacks/builder:base` | `BP_NODE_VERSION=20`      | npm run lint        | npm test + cov   | SonarQube + Trivy | Trivy          |
| Go       | `paketobuildpacks/builder:base` | `BP_GO_VERSION=1.21`      | golangci-lint       | go test -v -race | Trivy             | Trivy          |
| Ruby     | (future)                        | `BP_RUBY_VERSION=3.2`     | rubocop             | rspec            | brakeman          | bundler-audit  |

## Language Pack Structure

Each language pack lives in `pack/<language>/`:

```
pack/<language>/
├── buildpack.toml       # (optional) Buildpack config / buildpack.yml
├── env.toml             # Default BP_* environment variables
├── .woodpecker.template.yml # Pipeline template for this language
└── score.yaml           # Score spec for Dockerfile generation
```

**Key principle**: App teams do NOT write Dockerfiles. They provide:
1. Source code with language-specific build files (pom.xml, package.json, go.mod, etc.)
2. .fawkespipe.yml contract specifying builder: cnb and build env vars
3. A score.yaml for deployment-time Dockerfile generation

## Pipeline Contract (`.fawkespipe.yml.example`)

```yaml
build:
  builder: cnb                    # CNB is the primary builder
  cnb:
    builder: paketobuildpacks/builder:base
    env:
      BP_GO_VERSION: "1.21"
    # Optional: custom buildpacks
    buildpacks:
      - gcr.io/paketo-buildpacks/go
```

## Score Integration (Current)

For deployment targets requiring Docker images (K8s, VMs), Dockerfiles are generated from Score specs:

```yaml
# score.yaml (in app repo)
containers:
  app:
    image: ${IMAGE_TAG}
    # Score generates optimized Dockerfile from this spec
```

The pipeline's `buildImage` step handles both:
1. CNB build → produces OCI image directly (preferred)
2. If Dockerfile needed → `score-compose` or `score-k8s` generates it from score.yaml

## Currently Supported Languages

| Language        | Status      | CI Template          | Lint                | Test       | SAST              |
| --------------- | ----------- | -------------------- | ------------------- | ---------- | ----------------- |
| Java/Maven      | ✅          | `.woodpecker.yml` stages | checkstyle          | mvn test   | SonarQube         |
| Python/Flask    | 🔧 (DY-005) | Partial              | pylint/black/flake8 | pytest     | Bandit/safety     |
| Node.js/Express | ✅          | `.woodpecker.yml` stages | npm run lint        | npm test   | SonarQube + Trivy |
| Go              | ✅          | `.woodpecker.yml` stages | golangci-lint       | go test -v | Trivy             |
| Ruby            | ❌ Missing  | —                    | —                   | —          | —                 |

## Build Standards

### Pack CLI Arguments (CNB Build)

```bash
pack build ${IMAGE_TAG} \
  --builder ${CNB_BUILDER:-paketobuildpacks/builder:base} \
  ${buildpacksArg} \
  ${envArgs} \
  --verbose
```

### Score CLI (Dockerfile Generation)

```bash
# Generate Dockerfile for Docker Compose
score-compose generate --output docker-compose.generated.yml

# Generate K8s manifests
score-k8s generate --output k8s/
```

### Builder Selection

| Use Case         | Builder                                |
| ---------------- | -------------------------------------- |
| General polyglot | `paketobuildpacks/builder:base`        |
| Java-only        | `paketobuildpacks/builder-jammy-base`  |
| Minimal size     | `paketobuildpacks/builder-jammy-small` |
| Full toolchain   | `paketobuildpacks/builder-jammy-full`  |

## What You MAY Do

- Add new language packs in pack/<language>/ with buildpack.toml, env.toml, score.yaml
- Create example .fawkespipe.yml files in examples/
- Update .woodpecker.yml build stage for new builder options
- Create language-specific documentation in docs/packs/
- Define Score templates for Dockerfile generation

## What You MUST Ask Before

- Changing the default CNB builder version (affects all builds)
- Adding a buildpack that requires daemon access
- Removing a supported language from the pack matrix
- Modifying Score-to-Dockerfile generation logic

## What You MUST NEVER

- Pin a language version to a non-LTS release
- Add a buildpack that hasn't been tested with a full pipeline run
- Include proprietary or licensed buildpacks without maintainer approval
- Require app teams to write/maintain Dockerfiles (use CNB + Score)
