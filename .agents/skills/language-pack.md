---
name: language-pack
description: Buildpack configuration and language-specific build/test/scan patterns for uFawkesPipe. Defers to buildpack-agent for language matrix and implementation details.
applies: pack/**/*, examples/**/*.yml
---

# Language Pack — Buildpack Language Support

> Load this skill before creating a new language pack or example `.fawkespipe.yml`.
> **For the full language matrix and implementation details, see `buildpack-agent`.**

## Pack Directory Structure

```
pack/<language>/
├── Dockerfile           # (optional) Custom builder image
├── Jenkinsfile.template # Pipeline template copied to app repos
├── buildpack.toml       # (optional) Custom buildpack config
└── env.toml             # Default BP_* environment variables
```

## Adding a New Language

1. Create `pack/<language>/env.toml` with BP\_\* environment variables
2. Create `pack/<language>/Jenkinsfile.template` using the template below
3. Add a row to the language matrix in `buildpack-agent`
4. Create `examples/.fawkespipe-<language>.yml` with a working config
5. Test with: `pack build test-<language> --builder paketobuildpacks/builder:base`
6. Run `./scripts/validate-agents.sh` to verify consistency

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

## Validation Checklist for New Packs

- [ ] `env.toml` contains valid BP\_\* variables
- [ ] `Jenkinsfile.template` calls shared library steps
- [ ] Example `.fawkespipe-<language>.yml` parses as valid YAML
- [ ] `pack build` succeeds locally
- [ ] Lint step passes for the language
- [ ] Test step passes for the language
