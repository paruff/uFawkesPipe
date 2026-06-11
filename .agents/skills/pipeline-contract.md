---
name: pipeline-contract
description: .fawkespipe.yml (migrating from .deliveryd.yml) schema, validation, breaking change detection, and migration patterns for uFawkesPipe
applies: .fawkespipe.yml.example, examples/*.yml, Jenkinsfile, shared/vars/loadConfig.groovy
---

# Pipeline Contract — Schema and Migration

> Load this skill before modifying the pipeline contract or creating migrations.

## Contract File

The pipeline contract filename is `.fawkespipe.yml` (migrated from `.deliveryd.yml`).

## Schema Reference

```yaml
app:
  name: string # Required — application name
  type: string # Required — service | library | cli | frontend
  language: string # Required — java | python | nodejs | go | ruby
  version: string # Optional — semver, auto-generated if absent

build:
  builder: string # cnb | docker | custom
  image:
    registry: string # Default: docker.io
    namespace: string # Required
    name: string # Default: app.name
    tags: string[] # Tag strategy with variable substitution

stages:
  lint/enabled: bool # Default: true
  test/enabled: bool # Default: true
  sast/enabled: bool # Default: false
  dependency_scan/enabled: bool # Default: false
  build/enabled: bool # Default: true
  image_scan/enabled: bool # Default: false
  push/enabled: bool # Default: true

notifications: # Optional
kubernetes: # Optional
advanced: # Optional
```

## Breaking Change Rules

| Change                 | Type         | Migration                                  |
| ---------------------- | ------------ | ------------------------------------------ |
| Add new field          | Non-breaking | Default value required                     |
| Remove field           | **Breaking** | Deprecation notice + 1 week both supported |
| Rename field           | **Breaking** | Alias both names in parser                 |
| Change default value   | Non-breaking | Announce in changelog                      |
| Add new required field | **Breaking** | Major version bump                         |

## Deprecation Shim (in Jenkinsfile)

```groovy
// Support both old and new contract filenames during migration
def contractFile = '.fawkespipe.yml'
if (!fileExists(contractFile) && fileExists('.deliveryd.yml')) {
  echo "⚠️  DEPRECATED: '.deliveryd.yml' is renamed '.fawkespipe.yml'. " +
       "Support for .deliveryd.yml will be removed after 2026-06-14."
  contractFile = '.deliveryd.yml'
}
CONFIG = readYaml file: contractFile
```

## Validation

- All field names must be lowercase with underscores
- `app.name` must match regex `^[a-z0-9-]{3,48}$`
- `build.builder` must be one of: `cnb`, `docker`
- Tags with `${...}` variables resolve at pipeline runtime
- Unknown fields should warn but not fail (forward compatibility)

## Migration Checklist When Contract Changes

- [ ] Update `.fawkespipe.yml.example`
- [ ] Update all `examples/*.yml`
- [ ] Update `shared/vars/loadConfig.groovy`
- [ ] Add migration example to `examples/migrations/`
- [ ] Update `docs/PIPELINE_CONTRACT.md`
- [ ] Announce deprecation in `CHANGELOG.md`
- [ ] Verify: `grep -r "old-field-name" .` shows zero results in production files
