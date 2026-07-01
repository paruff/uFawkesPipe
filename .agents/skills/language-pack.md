---
name: language-pack
description: Buildpack configuration and language-specific build/test/scan patterns for uFawkesPipe. Defers to buildpack-agent for language matrix and implementation details.
applies: pack/*, examples/.fawkespipe-*.yml
---

# Language Pack — Buildpack Language Support

> Load this skill before creating a new language pack or example .fawkespipe.yml.
> **For the full language matrix and implementation details, see buildpack-agent.**

## Pack Directory Structure

```
pack/
├── Dockerfile           # (optional) Custom builder image
└── <language>/
    └── env.toml         # Default BP_* environment variables
```

The pipeline template is in `.woodpecker.yml` directly, not in the pack directory.

## Adding a New Language

1. Create `pack/<language>/env.toml` with BP_* environment variables
2. Update `.woodpecker.yml` with language-specific stages
3. Add a row to the language matrix in `buildpack-agent`
4. Create `examples/.fawkespipe-<language>.yml` with a working config
5. Test with: `pack build test-<language> --builder paketobuildpacks/builder:base`
6. Run `./scripts/validate-agents.sh` to verify consistency

## Example Pipeline Contract Pattern (.fawkespipe.yml — app teams create this)

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

## Woodpecker Pipeline Template (Current)

```yaml
# .woodpecker.yml step template for language-specific stages
- name: lint-<language>
  image: <language-builder-image>
  commands:
    - <lint-command>
  when:
    event: [push, pull_request]

- name: test-<language>
  image: <language-builder-image>
  commands:
    - <test-command>
  when:
    event: [push, pull_request]
```

## Validation Checklist for New Packs

- [ ] env.toml contains valid BP_* variables
- [ ] .woodpecker.yml defines language-specific stages
- [ ] Example .fawkespipe-<language>.yml parses as valid YAML
- [ ] pack build succeeds locally
- [ ] Lint step passes for the language
- [ ] Test step passes for the language
