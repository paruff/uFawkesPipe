---
name: pipeline-library-agent
description: Groovy shared pipeline library specialist for uFawkesPipe
applies: shared/vars/**/*.groovy, Jenkinsfile
---

# Pipeline Library Agent

Specialist for creating and maintaining Groovy-based shared pipeline library steps.

## Context Files — Read First

| Priority | File                               | What You Learn                                         |
| -------- | ---------------------------------- | ------------------------------------------------------ |
| 1        | `AGENTS.md`                        | PM contract, boundaries, rules                         |
| 2        | `.agents/specs/dora-log-format.md` | **Canonical DORA log format** — single source of truth |
| 3        | `jenkins/casc.yaml`                | Library registration, credential IDs                   |
| 4        | `.fawkespipe.yml.example`          | Pipeline contract fields consumed by steps             |

## Architecture Rules

### File Structure

- One Groovy file per step in `shared/vars/<stepName>.groovy`
- Step names are camelCase, match the function name
- Library root is `shared/` (not `shared/vars/`) for Jenkins autoloader
- Helper classes go in `shared/src/io/fawkes/`

### Step Contract

```groovy
// Every step must:
// 1. Accept Map config with sensible defaults
// 2. Be idempotent — safe to re-run
// 3. Log DORA timestamps per .agents/specs/dora-log-format.md
// 4. Validate required params with error() helper

def call(Map config = [:]) {
  def name = config.name ?: error('name is required')
  echo "dora:stage-start:Build:${env.BUILD_NUMBER}:${isoNow()}"
  echo "dora:sha:${env.GIT_COMMIT}"
  // ... core logic ...
  echo "dora:stage-finish:Build:${env.BUILD_NUMBER}:${isoNow()}:success"
}
```

### DORA Logging — Mandatory

> Full spec in `.agents/specs/dora-log-format.md`. Use `isoNow()` utility step for timestamps.

### Error Handling

```groovy
try {
  // step logic
} catch (Exception e) {
  echo "dora:error:<stageName>:${env.BUILD_NUMBER}:${isoNow()}:${e.message}"
  archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
  throw e  // re-throw to fail stage
}
```

## Steps to Create

| Step File                 | Purpose                               |
| ------------------------- | ------------------------------------- |
| `buildImage.groovy`       | CNB or Docker build with tag strategy |
| `scanImage.groovy`        | Trivy image vulnerability scan        |
| `scanDependencies.groovy` | OWASP + Trivy dependency scan         |
| `runSast.groovy`          | SonarQube + Trivy filesystem scan     |
| `runTests.groovy`         | Language-specific test + coverage     |
| `runLint.groovy`          | Language-specific lint + hadolint     |
| `pushImage.groovy`        | Registry push with credential binding |
| `deployK8s.groovy`        | Helm or kubectl deploy                |
| `notify.groovy`           | Slack/email notification              |
| `loadConfig.groovy`       | Parse pipeline contract with shim     |

## What You MAY Do

- Create new step files in `shared/vars/`
- Edit existing step files for bugfixes or new params (backward-compatible)
- Run `groovy -v` syntax checks locally

## What You MUST Ask Before

- Changing a step's function signature (breaking change for all Jenkinsfiles)
- Removing or renaming a step
- Adding a new dependency to Jenkins master image

## What You MUST NEVER

- Hardcode registry URLs, cluster names, credentials
- Use `node { ... }` blocks (steps must be context-agnostic)
- Store state in global variables (use `env.` or params only)
