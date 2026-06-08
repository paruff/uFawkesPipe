---
name: language-pack
description: Buildpack configuration and language-specific build/test/scan patterns for uFawkesPipe
applies: pack/**/*, examples/**/*.yml
---

# Language Pack — Buildpack Language Support

> Load this skill before creating a new language pack or example `.fawkespipe.yml`.

## Pack Directory Structure

```
pack/<language>/
├── Dockerfile           # (optional) Custom builder image
├── Jenkinsfile.template # Pipeline template copied to app repos
├── buildpack.toml       # (optional) Custom buildpack config
└── env.toml             # Default BP_* environment variables
```

## Language Matrix

| Language | Builder | Build Env Vars | Lint | Test | SAST | Dep Scan |
|---|---|---|---|---|---|---|
| Java | `paketobuildpacks/builder:base` | `BP_JVM_VERSION=17` | checkstyle | mvn test | SonarQube | OWASP + Trivy |
| Python | `paketobuildpacks/builder:base` | `BP_CPYTHON_VERSION=3.11` | pylint/black/flake8 | pytest + cov | Bandit | Safety + Trivy |
| Node.js | `paketobuildpacks/builder:base` | `BP_NODE_VERSION=20` | npm run lint | npm test + cov | SonarQube | Trivy |
| Go | `paketobuildpacks/builder:base` | `BP_GO_VERSION=1.21` | golangci-lint | go test -v -race | Trivy | Trivy |
| Ruby | (future) | `BP_RUBY_VERSION=3.2` | rubocop | rspec | brakeman | bundler-audit |

## Example `.fawkespipe.yml` Pattern

```yaml
app:
  name: my-<language>-app
  type: service
  language: <language>

build:
  builder: cnb
  cnb:
    builder: paketobuildpacks/builder:base
    env:
      <BP_VERSION_VAR>: "<version>"
  image:
    registry: docker.io
    namespace: myorg
    tags:
      - "${GIT_COMMIT_SHORT}"
      - "latest"

stages:
  lint:
    enabled: true
    commands:
      - language: <language>
        cmd: <lint-command>
  test:
    enabled: true
    commands:
      - language: <language>
        cmd: <test-command>
    coverage:
      enabled: true
      threshold: 70
  sast:
    enabled: true
    <tool-config>
  dependency_scan:
    enabled: true
    tools:
      - trivy
  build:
    enabled: true
  image_scan:
    enabled: true
    severity: CRITICAL
  push:
    enabled: true
```

## CI Template (Jenkinsfile.template)

Must call shared library steps:
```groovy
@Library('ufawkespipe-pipeline-library') _

pipeline {
  agent any
  stages {
    stage('Checkout') { steps { checkout scm } }
    stage('Validate') { steps { loadConfig() } }
    stage('Lint')     { steps { runLint() } }
    stage('Test')     { steps { runTests() } }
    stage('SAST')     { steps { runSast() } }
    stage('Dep Scan') { steps { scanDependencies() } }
    stage('Build')    { steps { buildImage() } }
    stage('Scan')     { steps { scanImage() } }
    stage('Push')     { steps { pushImage() } }
    stage('Deploy')   { steps { deployK8s() } }
  }
}
```
