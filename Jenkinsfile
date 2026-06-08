#!/usr/bin/env groovy

/**
 * uFawkesPipe Standard Pipeline
 * 
 * This Jenkinsfile implements the uFawkesPipe pipeline contract for polyglot applications.
 * It reads configuration from .deliveryd.yml and executes appropriate stages based on
 * the application type and language.
 * 
 * Supports: Java, Python, Node.js, Go, Ruby, and more
 * 
 * Pipeline Stages:
 * 1. Checkout - Clone the repository
 * 2. Load Config - Parse .deliveryd.yml contract
 * 3. Lint - Code quality and style checks
 * 4. Unit Test - Run unit tests and generate coverage
 * 5. SAST - Static Application Security Testing (SonarQube, Trivy)
 * 6. Dependency Scan - Vulnerability scanning (OWASP, Trivy)
 * 7. Build - Build container image using CNB or Docker
 * 8. Image Scan - Scan built image for vulnerabilities
 * 9. Push - Push image to registry (DockerHub)
 * 10. Deploy - Optional K8s deployment
 */

@Library('ufawkespipe-pipeline-library') _

pipeline {
    agent any
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 60, unit: 'MINUTES')
        timestamps()
        ansiColor('xterm')
    }
    
    environment {
        // Git info
        GIT_COMMIT_SHORT = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
        GIT_BRANCH = sh(script: "git rev-parse --abbrev-ref HEAD", returnStdout: true).trim()
        
        // Registry configuration
        DOCKER_REGISTRY = "${env.DOCKER_REGISTRY ?: 'docker.io'}"
        REGISTRY_CREDENTIALS = 'dockerhub-credentials'
        
        // Tool paths
        PACK_CLI = '/usr/local/bin/pack'
        DEPENDENCY_CHECK = '/usr/local/bin/dependency-check'
        
        // Build configuration (loaded from .deliveryd.yml)
        CONFIG = null
        APP_NAME = null
        APP_LANGUAGE = null
        IMAGE_TAG = null
    }
    
    stages {
        stage('Checkout') {
            steps {
                script {
                    echo "🔄 Checking out code..."
                    checkout scm
                    
                    // Display build information
                    sh """
                        echo "========================================"
                        echo "uFawkesPipe Pipeline - Build Information"
                        echo "========================================"
                        echo "Repository: ${env.GIT_URL}"
                        echo "Branch: ${GIT_BRANCH}"
                        echo "Commit: ${env.GIT_COMMIT}"
                        echo "Short Commit: ${GIT_COMMIT_SHORT}"
                        echo "========================================"
                    """
                }
            }
        }
        
        stage('Load Config') {
            steps {
                script {
                    echo "📋 Loading pipeline configuration from .deliveryd.yml..."
                    
                    if (!fileExists('.deliveryd.yml')) {
                        echo "⚠️  Warning: .deliveryd.yml not found. Using defaults."
                        // Set default configuration
                        CONFIG = [
                            app: [name: 'application', type: 'service', language: 'unknown'],
                            stages: [
                                lint: [enabled: false],
                                test: [enabled: false],
                                sast: [enabled: false],
                                dependency_scan: [enabled: false],
                                build: [enabled: true],
                                image_scan: [enabled: false],
                                push: [enabled: true]
                            ],
                            build: [
                                builder: 'cnb',
                                image: [
                                    registry: 'docker.io',
                                    namespace: env.DOCKERHUB_USERNAME ?: 'ufawkespipe',
                                    name: 'application'
                                ]
                            ]
                        ]
                    } else {
                        // Parse YAML configuration
                        CONFIG = readYaml file: '.deliveryd.yml'
                        echo "✅ Configuration loaded successfully"
                        echo "   App: ${CONFIG.app.name}"
                        echo "   Type: ${CONFIG.app.type}"
                        echo "   Language: ${CONFIG.app.language}"
                    }
                    
                    // Set environment variables from config
                    APP_NAME = CONFIG.app.name
                    APP_LANGUAGE = CONFIG.app.language
                    
                    // Build image tag
                    def imageNamespace = CONFIG.build?.image?.namespace ?: env.DOCKERHUB_USERNAME ?: 'ufawkespipe'
                    def imageName = CONFIG.build?.image?.name ?: APP_NAME
                    IMAGE_TAG = "${imageNamespace}/${imageName}:${GIT_COMMIT_SHORT}"
                    
                    echo "📦 Image will be tagged as: ${IMAGE_TAG}"
                }
            }
        }
        
        stage('Lint') {
            when {
                expression { CONFIG.stages?.lint?.enabled != false }
            }
            steps {
                script {
                    echo "🔍 Running lint checks..."
                    
                    def lintConfig = CONFIG.stages?.lint
                    def commands = lintConfig?.commands ?: []
                    
                    // Find command for current language
                    def lintCmd = commands.find { it.language == APP_LANGUAGE }
                    
                    if (lintCmd) {
                        try {
                            sh "${lintCmd.cmd}"
                            echo "✅ Lint passed"
                        } catch (Exception e) {
                            echo "❌ Lint failed: ${e.message}"
                            if (lintConfig?.strict != false) {
                                error("Lint stage failed")
                            }
                        }
                    } else {
                        echo "ℹ️  No lint configuration for language: ${APP_LANGUAGE}"
                    }
                    
                    // Dockerfile linting
                    if (lintConfig?.dockerfile?.enabled && fileExists('Dockerfile')) {
                        echo "🐳 Linting Dockerfile..."
                        try {
                            sh 'hadolint Dockerfile || true'
                        } catch (Exception e) {
                            echo "⚠️  Dockerfile lint warnings: ${e.message}"
                        }
                    }
                }
            }
        }
        
        stage('Unit Tests') {
            when {
                expression { CONFIG.stages?.test?.enabled != false }
            }
            steps {
                script {
                    echo "🧪 Running unit tests..."
                    
                    def testConfig = CONFIG.stages?.test
                    def commands = testConfig?.commands ?: []
                    
                    // Find command for current language
                    def testCmd = commands.find { it.language == APP_LANGUAGE }
                    
                    if (testCmd) {
                        try {
                            sh "${testCmd.cmd}"
                            echo "✅ Tests passed"
                            
                            // Publish coverage if enabled
                            if (testConfig?.coverage?.enabled) {
                                def reportFile = testConfig.coverage.report ?: 'coverage.xml'
                                if (fileExists(reportFile)) {
                                    echo "📊 Publishing coverage report..."
                                    // Coverage plugin would be configured here
                                }
                            }
                        } catch (Exception e) {
                            echo "❌ Tests failed: ${e.message}"
                            error("Test stage failed")
                        }
                    } else {
                        echo "ℹ️  No test configuration for language: ${APP_LANGUAGE}"
                    }
                }
            }
        }
        
        stage('SAST') {
            when {
                expression { CONFIG.stages?.sast?.enabled == true }
            }
            steps {
                script {
                    echo "🔒 Running Static Application Security Testing..."
                    
                    def sastConfig = CONFIG.stages?.sast
                    
                    // SonarQube scanning
                    if (sastConfig?.sonarqube?.enabled) {
                        echo "📊 Running SonarQube analysis..."
                        try {
                            withSonarQubeEnv('SonarQube') {
                                def projectKey = sastConfig.sonarqube.projectKey ?: APP_NAME
                                def sources = sastConfig.sonarqube.sources ?: 'src/'
                                
                                // Language-specific scanner
                                switch(APP_LANGUAGE) {
                                    case 'java':
                                        sh "mvn sonar:sonar -Dsonar.projectKey=${projectKey}"
                                        break
                                    case 'nodejs':
                                        sh "npm run sonar || npx sonarqube-scanner -Dsonar.projectKey=${projectKey}"
                                        break
                                    default:
                                        sh """
                                            sonar-scanner \
                                                -Dsonar.projectKey=${projectKey} \
                                                -Dsonar.sources=${sources} \
                                                -Dsonar.host.url=http://sonarqube:9000
                                        """
                                }
                            }
                            
                            // Wait for quality gate if configured
                            if (sastConfig.sonarqube.qualityGate) {
                                timeout(time: 10, unit: 'MINUTES') {
                                    def qg = waitForQualityGate()
                                    if (qg.status != 'OK') {
                                        error "Quality gate failed: ${qg.status}"
                                    }
                                }
                            }
                        } catch (Exception e) {
                            echo "⚠️  SonarQube analysis failed: ${e.message}"
                        }
                    }
                    
                    // Trivy filesystem scan
                    if (sastConfig?.trivy?.enabled) {
                        echo "🔍 Running Trivy filesystem scan..."
                        try {
                            def severity = sastConfig.trivy.severity ?: 'HIGH,CRITICAL'
                            sh """
                                trivy fs --severity ${severity} \
                                    --format json \
                                    --output trivy-fs-report.json \
                                    . || true
                            """
                            archiveArtifacts artifacts: 'trivy-fs-report.json', allowEmptyArchive: true
                        } catch (Exception e) {
                            echo "⚠️  Trivy scan failed: ${e.message}"
                        }
                    }
                }
            }
        }
        
        stage('Dependency Scan') {
            when {
                expression { CONFIG.stages?.dependency_scan?.enabled == true }
            }
            steps {
                script {
                    echo "🔍 Scanning dependencies for vulnerabilities..."
                    
                    def scanConfig = CONFIG.stages?.dependency_scan
                    def tools = scanConfig?.tools ?: ['owasp-dependency-check']
                    
                    // OWASP Dependency-Check
                    if ('owasp-dependency-check' in tools) {
                        echo "🛡️  Running OWASP Dependency-Check..."
                        try {
                            def suppressions = scanConfig?.suppressions ?: ''
                            def suppressionArg = suppressions ? "--suppression ${suppressions}" : ''
                            
                            sh """
                                ${DEPENDENCY_CHECK} \
                                    --scan . \
                                    --format JSON \
                                    --format HTML \
                                    --out ./dependency-check-report \
                                    ${suppressionArg} \
                                    --failOnCVSS 7 || true
                            """
                            
                            archiveArtifacts artifacts: 'dependency-check-report/*', allowEmptyArchive: true
                            publishHTML([
                                reportDir: 'dependency-check-report',
                                reportFiles: 'dependency-check-report.html',
                                reportName: 'OWASP Dependency-Check Report',
                                keepAll: true
                            ])
                        } catch (Exception e) {
                            echo "⚠️  Dependency-Check completed with warnings: ${e.message}"
                        }
                    }
                    
                    // Trivy dependency scan
                    if ('trivy' in tools) {
                        echo "🔍 Running Trivy dependency scan..."
                        try {
                            sh """
                                trivy fs --scanners vuln \
                                    --format json \
                                    --output trivy-dep-report.json \
                                    . || true
                            """
                            archiveArtifacts artifacts: 'trivy-dep-report.json', allowEmptyArchive: true
                        } catch (Exception e) {
                            echo "⚠️  Trivy dependency scan failed: ${e.message}"
                        }
                    }
                    
                    echo "✅ Dependency scan completed"
                }
            }
        }
        
        stage('Build') {
            when {
                expression { CONFIG.stages?.build?.enabled != false }
            }
            steps {
                script {
                    echo "🏗️  Building container image..."
                    
                    def buildConfig = CONFIG.build
                    def builder = buildConfig?.builder ?: 'cnb'
                    
                    if (builder == 'cnb') {
                        echo "📦 Building with Cloud Native Buildpacks..."
                        
                        def cnbBuilder = buildConfig?.cnb?.builder ?: env.CNB_BUILDER ?: 'paketobuildpacks/builder:base'
                        def buildpacks = buildConfig?.cnb?.buildpacks ?: []
                        def buildpacksArg = buildpacks ? buildpacks.collect { "--buildpack ${it}" }.join(' ') : ''
                        
                        // Set build-time environment variables
                        def envVars = buildConfig?.cnb?.env ?: [:]
                        def envArgs = envVars.collect { k, v -> "--env ${k}=${v}" }.join(' ')
                        
                        sh """
                            ${PACK_CLI} build ${IMAGE_TAG} \
                                --builder ${cnbBuilder} \
                                ${buildpacksArg} \
                                ${envArgs} \
                                --verbose
                        """
                        
                    } else if (builder == 'docker') {
                        echo "🐳 Building with Docker..."
                        
                        def dockerfile = buildConfig?.docker?.dockerfile ?: 'Dockerfile'
                        def context = buildConfig?.docker?.context ?: '.'
                        def target = buildConfig?.docker?.target ?: ''
                        def targetArg = target ? "--target ${target}" : ''
                        
                        def buildArgs = buildConfig?.docker?.buildArgs ?: [:]
                        def buildArgsStr = buildArgs.collect { k, v -> "--build-arg ${k}=${v}" }.join(' ')
                        
                        sh """
                            docker build \
                                -f ${dockerfile} \
                                -t ${IMAGE_TAG} \
                                ${targetArg} \
                                ${buildArgsStr} \
                                ${context}
                        """
                    }
                    
                    echo "✅ Image built: ${IMAGE_TAG}"
                    
                    // Tag with additional tags
                    def tags = buildConfig?.image?.tags ?: []
                    tags.each { tag ->
                        def resolvedTag = tag
                            .replace('${GIT_COMMIT_SHORT}', GIT_COMMIT_SHORT)
                            .replace('${GIT_BRANCH}', GIT_BRANCH)
                            .replace('${APP_NAME}', APP_NAME)
                        
                        if (resolvedTag != GIT_COMMIT_SHORT) {
                            def fullTag = "${buildConfig?.image?.namespace ?: env.DOCKERHUB_USERNAME}/${buildConfig?.image?.name ?: APP_NAME}:${resolvedTag}"
                            sh "docker tag ${IMAGE_TAG} ${fullTag}"
                            echo "🏷️  Tagged: ${fullTag}"
                        }
                    }
                }
            }
        }
        
        stage('Image Scan') {
            when {
                expression { CONFIG.stages?.image_scan?.enabled == true }
            }
            steps {
                script {
                    echo "🔍 Scanning container image for vulnerabilities..."
                    
                    def scanConfig = CONFIG.stages?.image_scan
                    def severity = scanConfig?.severity ?: 'HIGH,CRITICAL'
                    
                    try {
                        sh """
                            trivy image --severity ${severity} \
                                --format json \
                                --output trivy-image-report.json \
                                ${IMAGE_TAG} || true
                        """
                        
                        archiveArtifacts artifacts: 'trivy-image-report.json', allowEmptyArchive: true
                        
                        // Parse results and fail if critical vulnerabilities found
                        def failOn = scanConfig?.fail_on ?: 'CRITICAL'
                        if (failOn) {
                            sh """
                                trivy image --severity ${failOn} \
                                    --exit-code 1 \
                                    ${IMAGE_TAG}
                            """
                        }
                        
                        echo "✅ Image scan completed"
                    } catch (Exception e) {
                        echo "⚠️  Image scan found vulnerabilities: ${e.message}"
                        if (scanConfig?.strict != false) {
                            error("Critical vulnerabilities found in image")
                        }
                    }
                }
            }
        }
        
        stage('Push') {
            when {
                expression { CONFIG.stages?.push?.enabled != false }
            }
            steps {
                script {
                    echo "📤 Pushing image to registry..."
                    
                    docker.withRegistry("https://${DOCKER_REGISTRY}", REGISTRY_CREDENTIALS) {
                        // Push all tags
                        def buildConfig = CONFIG.build
                        def namespace = buildConfig?.image?.namespace ?: env.DOCKERHUB_USERNAME
                        def imageName = buildConfig?.image?.name ?: APP_NAME
                        def tags = buildConfig?.image?.tags ?: [GIT_COMMIT_SHORT, 'latest']
                        
                        tags.each { tag ->
                            def resolvedTag = tag
                                .replace('${GIT_COMMIT_SHORT}', GIT_COMMIT_SHORT)
                                .replace('${GIT_BRANCH}', GIT_BRANCH)
                                .replace('${APP_NAME}', APP_NAME)
                            
                            def fullTag = "${namespace}/${imageName}:${resolvedTag}"
                            
                            sh "docker push ${fullTag}"
                            echo "✅ Pushed: ${fullTag}"
                        }
                    }
                    
                    echo "🎉 All images pushed successfully"
                }
            }
        }
        
        stage('Deploy to K8s') {
            when {
                expression { CONFIG.kubernetes?.enabled == true }
            }
            steps {
                script {
                    echo "🚀 Deploying to Kubernetes..."
                    
                    def k8sConfig = CONFIG.kubernetes
                    def namespace = k8sConfig?.namespace ?: 'default'
                    
                    if (k8sConfig?.helm?.enabled) {
                        echo "⎈ Deploying with Helm..."
                        def chart = k8sConfig.helm.chart
                        def release = k8sConfig.helm.release ?: APP_NAME
                        def values = k8sConfig.helm.values ?: ''
                        def valuesArg = values ? "-f ${values}" : ''
                        
                        sh """
                            helm upgrade --install ${release} ${chart} \
                                --namespace ${namespace} \
                                --set image.tag=${GIT_COMMIT_SHORT} \
                                ${valuesArg}
                        """
                    } else if (k8sConfig?.manifests?.path) {
                        echo "☸️  Applying Kubernetes manifests..."
                        def manifestPath = k8sConfig.manifests.path
                        
                        sh """
                            kubectl apply -f ${manifestPath} \
                                --namespace ${namespace}
                        """
                    }
                    
                    echo "✅ Deployment completed"
                }
            }
        }
    }
    
    post {
        always {
            script {
                echo "🧹 Cleaning up..."
                
                // Clean workspace if configured
                if (CONFIG?.advanced?.workspace?.cleanup != false) {
                    cleanWs()
                }
            }
        }
        success {
            script {
                echo "✅ Pipeline completed successfully!"
                echo "📦 Image: ${IMAGE_TAG}"
                
                // Send notifications if configured
                def notifications = CONFIG?.notifications
                if (notifications?.slack?.enabled && 'build_success' in (notifications.slack.events ?: [])) {
                    // slackSend channel: notifications.slack.channel, message: "✅ Build succeeded: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
                    echo "Would send Slack notification (not configured)"
                }
            }
        }
        failure {
            script {
                echo "❌ Pipeline failed!"
                
                // Send notifications if configured
                def notifications = CONFIG?.notifications
                if (notifications?.slack?.enabled && 'build_failure' in (notifications.slack.events ?: [])) {
                    // slackSend channel: notifications.slack.channel, message: "❌ Build failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
                    echo "Would send Slack notification (not configured)"
                }
                
                if (notifications?.email?.enabled && 'build_failure' in (notifications.email.events ?: [])) {
                    // emailext to: notifications.email.recipients, subject: "Build Failed: ${env.JOB_NAME}", body: "Build failed."
                    echo "Would send email notification (not configured)"
                }
            }
        }
    }
}
