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

  // 2. Log start
  echo "stage-start:${isoNow()} step:myStep param1=${config.param1}"

  // 3. Idempotency check — skip if already done
  if (fileExists('.myStep-completed')) {
    echo "myStep: already completed, skipping"
    return
  }

  // 4. Core logic with error handling
  try {
    sh "some-command ${required}"
    writeFile file: '.myStep-completed', text: 'done'
    echo "stage-finish:${isoNow()} step:myStep result:success"
  } catch (Exception e) {
    echo "stage-finish:${isoNow()} step:myStep result:failure error:${e.message}"
    archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
    throw e
  }
}

// Utility — available to all steps in vars/
String isoNow() {
  return new Date().format("yyyy-MM-dd'T'HH:mm:ss'Z'", TimeZone.getTimeZone('UTC'))
}
```

## DORA Logging — Strict Rules

| Field | Format | Example |
|---|---|---|
| Stage start | `stage-start:<ISO timestamp> step:<name>` | `stage-start:2026-06-07T12:00:00Z step:buildImage` |
| SHA | `sha:<commit hash>` | `sha:abc123def456` |
| Stage finish | `stage-finish:<ISO timestamp> step:<name> result:<result>` | `stage-finish:2026-06-07T12:05:00Z step:buildImage result:success` |

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
// ✅ CORRECT
withCredentials([usernamePassword(
  credentialsId: 'dockerhub-credentials',
  usernameVariable: 'DOCKER_USER',
  passwordVariable: 'DOCKER_PASS'
)]) {
  sh "docker login -u ${DOCKER_USER} -p ${DOCKER_PASS}"
}

// ❌ WRONG — never inline
sh "docker login -u myuser -p mypassword"
```

## Error Handling

```groovy
try {
  sh "command-that-may-fail"
} catch (Exception e) {
  // ALWAYS capture artifacts before re-throwing
  archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
  junit allowEmptyResults: true, testResults: 'reports/junit/*.xml'
  echo "stage-finish:${isoNow()} step:name result:failure error:${e.message}"
  throw e
}
```
