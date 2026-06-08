---
name: Jenkins Pipeline Instructions
description: Applied automatically when working on Jenkinsfile or shared/ library
applyTo: "Jenkinsfile,shared/**/*.groovy,jenkins/**/*.groovy"
---

# Jenkins Pipeline Instructions — uFawkesPipe

## Read First
- `AGENTS.md` → Jenkinsfile and Shared Library rules
- `.fawkespipe.yml.example` → the pipeline contract app teams use

## DORA Logging — Required on Every Stage

```groovy
// ✅ Every stage must log start, SHA, finish
stage('Build') {
  steps {
    script {
      echo "stage-start:${new Date().format("yyyy-MM-dd'T'HH:mm:ss'Z'", TimeZone.getTimeZone('UTC'))}"
      echo "sha:${env.GIT_COMMIT}"
      // ... stage steps ...
      echo "stage-finish:${new Date().format("yyyy-MM-dd'T'HH:mm:ss'Z'", TimeZone.getTimeZone('UTC'))}"
    }
  }
}
```

## Standard Pipeline Stage Order

```groovy
pipeline {
  agent any
  stages {
    stage('Checkout')      { ... }  // 1. Source
    stage('Validate')      { ... }  // 2. Config validation
    stage('Build')         { ... }  // 3. Compile / image build
    stage('Test')          { ... }  // 4. Unit + integration
    stage('Security Scan') { ... }  // 5. SAST / dependency scan
    stage('Publish')       { ... }  // 6. Push image to registry
    stage('Deploy')        { ... }  // 7. Deploy to environment
  }
  post {
    always { archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true }
    failure { echo "Pipeline failed at stage: ${env.STAGE_NAME}" }
  }
}
```

## No Inline Credentials

```groovy
// ✅ Use withCredentials block
stage('Publish') {
  steps {
    withCredentials([usernamePassword(
      credentialsId: 'docker-registry',
      usernameVariable: 'REGISTRY_USER',
      passwordVariable: 'REGISTRY_PASS'
    )]) {
      sh 'docker login -u $REGISTRY_USER -p $REGISTRY_PASS $REGISTRY_URL'
    }
  }
}

// ❌ Never
stage('Publish') {
  steps {
    sh 'docker login -u myuser -p mypassword registry.example.com'
  }
}
```

## Shared Library Step Pattern

```groovy
// shared/vars/buildImage.groovy
// One file per step. Steps are idempotent.
def call(Map config = [:]) {
  def imageName = config.imageName ?: error('imageName required')
  def imageTag  = config.imageTag  ?: env.BUILD_NUMBER

  echo "buildImage: start — ${imageName}:${imageTag}"
  sh "docker build -t ${imageName}:${imageTag} ."
  echo "buildImage: finish — ${imageName}:${imageTag}"
}
```

## Error Handling — Capture Artifacts Before Failing

```groovy
stage('Test') {
  steps {
    script {
      try {
        sh 'make test'
      } catch (err) {
        // Capture test results even on failure
        junit allowEmptyResults: true, testResults: 'reports/junit/*.xml'
        throw err  // re-throw to fail the stage
      }
    }
  }
  post {
    always {
      junit allowEmptyResults: true, testResults: 'reports/junit/*.xml'
    }
  }
}
```

## Timeouts — Required on Long-Running Stages

```groovy
stage('Security Scan') {
  options { timeout(time: 10, unit: 'MINUTES') }
  steps { ... }
}
```
