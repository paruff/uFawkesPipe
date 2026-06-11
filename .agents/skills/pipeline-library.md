---
name: pipeline-library
description: Groovy shared library conventions, DORA logging, step patterns, and idempotency rules for uFawkesPipe
applies: shared/vars/**/*.groovy, Jenkinsfile
---

# Pipeline Library — Groovy Shared Library Standards

> Load this skill before creating or editing any `shared/vars/` Groovy file.

## File Convention

- One step per file in `shared/vars/<stepName>.groovy`
- Step `foo` is callable in Jenkinsfiles as `foo(configMap)`
- The filename (minus `.groovy`) IS the function name — no renaming without breaking changes
- Helper classes go in `shared/src/io/fawkes/` and are imported via `import io.fawkes.Helper`

## Step Template

```groovy
// shared/vars/myStep.groovy
// Description: What this step does

def call(Map config = [:]) {
  // 1. Validate required params
  def required = config.requiredParam ?: error('myStep: requiredParam is required')

  // 2. Log start per .agents/specs/dora-log-format.md
  echo "dora:stage-start:MyStep:${env.BUILD_NUMBER}:${isoNow()}"

  // 3. Idempotency check — skip if already done
  if (fileExists('.myStep-completed')) {
    echo "myStep: already completed, skipping"
    return
  }

  // 4. Core logic with error handling
  try {
    sh "some-command ${required}"
    writeFile file: '.myStep-completed', text: 'done'
    echo "dora:stage-finish:MyStep:${env.BUILD_NUMBER}:${isoNow()}:success"
  } catch (Exception e) {
    echo "dora:error:MyStep:${env.BUILD_NUMBER}:${isoNow()}:${e.message}"
    archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
    throw e
  }
}
```

## DORA Logging — Strict Rules

> Full spec in `.agents/specs/dora-log-format.md`. Use `isoNow()` utility step for timestamps.

| Rule         | Details                                    |
| ------------ | ------------------------------------------ |
| Prefix       | All lines MUST start with `dora:`          |
| Delimiter    | Colon-delimited fields                     |
| Timestamps   | ISO 8601 UTC via `isoNow()`                |
| Build number | Include `env.BUILD_NUMBER` in stage events |
| No PII       | Never log credentials, tokens, or secrets  |

## Idempotency Patterns

### Pattern 1: Marker File (preferred)

```groovy
if (fileExists('.step-done')) { return }
sh "..."
writeFile file: '.step-done', text: 'done'
```

### Pattern 2: Check Output

```groovy
def result = sh(script: "some-check-command", returnStdout: true).trim()
if (result == 'already-done') { return }
```

## Credential Handling

```groovy
// ✅ CORRECT — credentials stay in Jenkins credential store
withCredentials([usernamePassword(
  credentialsId: 'dockerhub-credentials',
  usernameVariable: 'DOCKER_USER',
  passwordVariable: 'DOCKER_PASS' # pragma: allowlist secret
)]) {
  // Use stdin to avoid exposing password in process table # pragma: allowlist secret
  sh "echo \${DOCKER_PASS} | docker login -u \${DOCKER_USER} --password-stdin"
}

// ❌ WRONG — password visible in process table
sh "docker login -u myuser -p mypassword"

// ❌ WRONG — password visible in shell expansion
sh "docker login -u ${DOCKER_USER} -p ${DOCKER_PASS}"
```

## Error Handling

```groovy
try {
  sh "command-that-may-fail"
} catch (Exception e) {
  // ALWAYS capture artifacts before re-throwing
  archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
  junit allowEmptyResults: true, testResults: 'reports/junit/*.xml'
  echo "dora:error:<stageName>:${env.BUILD_NUMBER}:${isoNow()}:${e.message}"
  throw e
}
```
