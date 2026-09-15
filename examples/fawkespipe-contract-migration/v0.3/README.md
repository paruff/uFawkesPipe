# Pipeline Contract Migration — v0.2 → v0.3

This example demonstrates the field changes from v0.2 to v0.3 of the `.fawkespipe.yml` contract.

## Key Changes

### 1. SonarQube Quality Gate (NEW)

v0.3 adds `sonarqube.qualityGate` to control whether the pipeline waits for SonarQube quality gate results.

```yaml
# v0.2 (no quality gate control)
stages:
  sast:
    enabled: true

# v0.3 (with quality gate control)
stages:
  sast:
    enabled: true
    sonarqube:
      enabled: true
      qualityGate: true  # Wait for quality gate result
      projectKey: my-app
      sources: src/
      exclusions: "**/test/**,**/tests/**"
```

### 2. Security Stage Integration (NEW)

v0.3 integrates security scanning directly into the pipeline contract:

```yaml
stages:
  sast:
    enabled: true
    sonarqube:
      enabled: true
      qualityGate: true
    trivy:
      enabled: true
      severity: HIGH,CRITICAL
```

### 3. DefectDojo Upload (NEW)

v0.3 includes automatic upload of security scan results to DefectDojo:

```yaml
stages:
  # ... other stages ...
  push:
    enabled: true
    defectdojo:
      enabled: true
      engagement: CI-Engagement
```

## Migration Steps

1. **Add SonarQube quality gate configuration:**
   ```yaml
   stages:
     sast:
       enabled: true
       sonarqube:
         qualityGate: true
   ```

2. **Add Trivy configuration to SAST stage:**
   ```yaml
   stages:
     sast:
       enabled: true
       trivy:
         enabled: true
         severity: HIGH,CRITICAL
   ```

3. **Regenerate pipeline:**
   ```bash
   make generate-pipeline
   ```

4. **Verify generated output:**
   ```bash
   make check-pipeline
   ```

## Example Files

- `.fawkespipe.yml` — v0.3 contract example
- `.woodpecker.yml` — Generated pipeline (do not edit manually)

## Validation

```bash
# Validate the contract
python scripts/generate_woodpecker_yml.py --check \
  --contract examples/fawkespipe-contract-migration/v0.3/.fawkespipe.yml \
  --output examples/fawkespipe-contract-migration/v0.3/.woodpecker.yml
```
