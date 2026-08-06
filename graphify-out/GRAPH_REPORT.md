# Graph Report - uFawkesPipe  (2026-08-06)

## Corpus Check
- 63 files · ~53,691 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1128 nodes · 1212 edges · 78 communities (64 shown, 14 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 36 edges (avg confidence: 0.82)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `246a5819`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Platform Architecture|Platform Architecture]]
- [[_COMMUNITY_Agent Stack & DORA|Agent Stack & DORA]]
- [[_COMMUNITY_Pipeline Structure Tests|Pipeline Structure Tests]]
- [[_COMMUNITY_Compose Validation Tests|Compose Validation Tests]]
- [[_COMMUNITY_Compose Network Tests|Compose Network Tests]]
- [[_COMMUNITY_DefectDojo Upload Tests|DefectDojo Upload Tests]]
- [[_COMMUNITY_Notify-OBS Telemetry|Notify-OBS Telemetry]]
- [[_COMMUNITY_Legacy Jenkins Library|Legacy Jenkins Library]]
- [[_COMMUNITY_Woodpecker Config Tests|Woodpecker Config Tests]]
- [[_COMMUNITY_SonarQube Fixtures|SonarQube Fixtures]]
- [[_COMMUNITY_Test Fixtures Config|Test Fixtures Config]]
- [[_COMMUNITY_Trivy FS Scan Tests|Trivy FS Scan Tests]]
- [[_COMMUNITY_Stack Health Tests|Stack Health Tests]]
- [[_COMMUNITY_Pipeline Contract Tests|Pipeline Contract Tests]]
- [[_COMMUNITY_Image Signing Tests|Image Signing Tests]]
- [[_COMMUNITY_Trivy Image Scan Tests|Trivy Image Scan Tests]]
- [[_COMMUNITY_SBOM Generation Tests|SBOM Generation Tests]]
- [[_COMMUNITY_Service Auth Tests|Service Auth Tests]]
- [[_COMMUNITY_Suite Behavior Tests|Suite Behavior Tests]]
- [[_COMMUNITY_Validate Agents Step|Validate Agents Step]]
- [[_COMMUNITY_Dependency Automation|Dependency Automation]]
- [[_COMMUNITY_Artifact Init Tests|Artifact Init Tests]]
- [[_COMMUNITY_Gitleaks Secrets Scan|Gitleaks Secrets Scan]]
- [[_COMMUNITY_Portainer CD Tests|Portainer CD Tests]]
- [[_COMMUNITY_Compose Integration|Compose Integration]]
- [[_COMMUNITY_Full Pipeline E2E|Full Pipeline E2E]]
- [[_COMMUNITY_SonarQube Health|SonarQube Health]]
- [[_COMMUNITY_Woodpecker Health|Woodpecker Health]]
- [[_COMMUNITY_Language Contracts|Language Contracts]]
- [[_COMMUNITY_SonarQube Simulation|SonarQube Simulation]]
- [[_COMMUNITY_DORA Log Script|DORA Log Script]]
- [[_COMMUNITY_Contributing & Policy|Contributing & Policy]]
- [[_COMMUNITY_Pre-flight Validation|Pre-flight Validation]]
- [[_COMMUNITY_CI Diagnosis & Fix|CI Diagnosis & Fix]]
- [[_COMMUNITY_OpenCode Config|OpenCode Config]]
- [[_COMMUNITY_OpenCode Plugin|OpenCode Plugin]]
- [[_COMMUNITY_Tests Package Init|Tests Package Init]]
- [[_COMMUNITY_Tests Package Init 2|Tests Package Init 2]]
- [[_COMMUNITY_Graphify Plugin|Graphify Plugin]]
- [[_COMMUNITY_Commit Message Hook|Commit Message Hook]]
- [[_COMMUNITY_Pre-commit Hook|Pre-commit Hook]]
- [[_COMMUNITY_Quickstart Smoke Test|Quickstart Smoke Test]]
- [[_COMMUNITY_Validate Agents Hook|Validate Agents Hook]]
- [[_COMMUNITY_Tests Package Init 3|Tests Package Init 3]]
- [[_COMMUNITY_Test Fixtures|Test Fixtures]]
- [[_COMMUNITY_Project Meta|Project Meta]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 94|Community 94]]

## God Nodes (most connected - your core abstractions)
1. `TestUploadDefectDojoStep` - 18 edges
2. `Acceptance Criteria — uFawkesPipe v0.3` - 18 edges
3. `uFawkesPipe` - 17 edges
4. `TestNotifyObsStep` - 17 edges
5. `DORA Logging Anchor` - 14 edges
6. `uFawkesPipe — Architecture` - 13 edges
7. `TestVulnScanFsStep` - 13 edges
8. `uFawkesPipe — Implementation Plan v0.2` - 13 edges
9. `AGENTS.md — uFawkesPipe` - 12 edges
10. `TestVulnScanImageStep` - 12 edges

## Surprising Connections (you probably didn't know these)
- `Pre-flight Checks Job` --semantically_similar_to--> `Gitleaks Scan Anchor`  [INFERRED] [semantically similar]
  .github/workflows/reusable-preflight.yml → .woodpecker/steps/common.yaml
- `Reusable Rollback Workflow` --conceptually_related_to--> `DORA Logging Anchor`  [INFERRED]
  .github/workflows/reusable-rollback.yml → .woodpecker/steps/common.yaml
- `CI Workflow` --references--> `DORA Log Format Spec`  [INFERRED]
  .github/workflows/ci.yml → .agents/specs/dora-log-format.md
- `CI Tests Workflow` --references--> `DORA Log Format Spec`  [INFERRED]
  .github/workflows/ci-tests.yml → .agents/specs/dora-log-format.md
- `Reusable Build Workflow` --references--> `DORA Log Format Spec`  [INFERRED]
  .github/workflows/reusable-build.yml → .agents/specs/dora-log-format.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Suite Mode Integration (uFawkesRes + uFawkesObs)** — readme_suite_mode, compose_suite_compose_overlay, readme_ufawkesres, readme_ufawkesobs, agents_observability_agent_opentelemetry [EXTRACTED 1.00]
- **Security-First Pipeline** — readme_security_stage, readme_gitleaks_secrets_scan, readme_trivy_vuln_scan, readme_sonarqube_sast, readme_defectdojo_integration [EXTRACTED 1.00]
- **DORA Observability Pipeline** — agents_observability_agent_dora_metrics, agents_observability_agent_opentelemetry, agents_observability_agent_dora_log_format, readme_notify_obs_step, readme_ufawkesobs [EXTRACTED 0.95]
- **CI Pipeline Stage Flow** — github_workflows_ci_pipeline, github_workflows_reusable_dependency_review, github_workflows_reusable_build, github_workflows_ci_tests [EXTRACTED 1.00]
- **DORA Observability Standard** — agents_specs_dora_log_format, agents_skills_pipeline_library, agents_pipeline_library_agent, agents_orchestrator_agent [INFERRED 0.85]
- **Orchestrated Agent Team** — agents_orchestrator_agent, agents_pipeline_library_agent, agents_security_agent, agents_smoke_test_agent, agents_workflow_agent [EXTRACTED 1.00]
- **DORA Observability Flow** — steps_common_dora_logging, steps_common_notify_obs, docs_metrics_dora_metrics, docs_architecture_telemetry, docs_architecture_ufawkesobs [EXTRACTED 1.00]
- **Security Scanning Pipeline** — steps_common_gitleaks_scan, steps_common_trivy_fs, steps_common_trivy_image, steps_common_defectdojo_upload, workflows_reusable_security_scanning [INFERRED 0.85]
- **Jenkins to Woodpecker Migration** — history_jenkins_migration, docs_architecture_legacy_jenkins, docs_architecture_woodpecker_stack, docs_webhook_api [EXTRACTED 1.00]
- **Polyglot Pipeline Contract Examples** — examples_fawkespipe_go_contract, examples_fawkespipe_java_maven_contract, examples_fawkespipe_nodejs_express_contract, examples_fawkespipe_python_flask_contract [INFERRED 0.95]

## Communities (78 total, 14 thin omitted)

### Community 0 - "Platform Architecture"
Cohesion: 0.06
Nodes (47): Change Impact Map — uFawkesPipe, Compose (standalone mode — compose.yaml), Compose (suite mode — compose.suite.yaml), Cross-Plane Impact, Pipeline Contract (.fawkespipe.yml), Pipeline Definition (.woodpecker.yml), Architecture & Documentation, Current Limitations (+39 more)

### Community 1 - "Agent Stack & DORA"
Cohesion: 0.29
Nodes (8): compose.yaml Stack, portainer service, sonarqube service, Suite Mode Compose Overlay, woodpecker-agent service, woodpecker-server service, PIPE-004 Design: workflow-agent.md Stale Ref Fix, PIPE-004 Specification

### Community 2 - "Pipeline Structure Tests"
Cohesion: 0.05
Nodes (24): Acceptance tests: Pipeline structure verification.  Covers AC-08, AC-09, AC-12 (, Global when condition must exist., Verify security gate configuration (AC-09)., Secrets-scan must use gitleaks with --exit-code=1., vuln-scan-fs must not have a branch constraint., vuln-scan-image must be constrained to main branch., Verify observability/deployment event step (AC-12)., notify-obs step must be present in deploy stage. (+16 more)

### Community 3 - "Compose Validation Tests"
Cohesion: 0.10
Nodes (11): Unit tests for compose.yaml configuration validation., compose.yaml must be valid YAML., compose.yaml must have a services section., Every service must have an 'image' specified., No service should use ':latest' image tags., Every service must have plane/managed-by labels., Top-level volumes must be declared., No hardcoded secrets or credentials in compose.yaml. (+3 more)

### Community 4 - "Compose Network Tests"
Cohesion: 0.06
Nodes (24): compose_config(), makefile_content(), Automated acceptance test for WP-002: fawkes-net external network  Validates the, Acceptance: suite fawkes-net has external: true., Acceptance: suite fawkes-net has name: fawkes-net., Acceptance: All four services attach to fawkes-net in suite mode., Acceptance: suite woodpecker-agent has         WOODPECKER_BACKEND_DOCKER_NETWORK, Validate Makefile network target and suite dependency. (+16 more)

### Community 5 - "DefectDojo Upload Tests"
Cohesion: 0.06
Nodes (18): Acceptance: upload-defectdojo step (WP-005) is correctly configured., Helper: find the upload-defectdojo step by name., Acceptance: Step named 'upload-defectdojo' exists in steps list., Acceptance: upload-defectdojo uses 'curlimages/curl:8.6.0'., Acceptance: upload-defectdojo has DOJO_API_TOKEN from_secret., Acceptance: upload-defectdojo has when: branch: main condition., Acceptance: upload-defectdojo loops over gitleaks artifacts., Acceptance: upload-defectdojo loops over trivy-repo artifacts. (+10 more)

### Community 6 - "Notify-OBS Telemetry"
Cohesion: 0.06
Nodes (17): Acceptance: notify-obs step (WP-006) is correctly configured., Helper: find the notify-obs step by name., Acceptance: Step named 'notify-obs' exists in steps list., Acceptance: notify-obs uses 'curlimages/curl:8.6.0'., Acceptance: notify-obs has when: branch: main condition., Acceptance: notify-obs has OTEL_ENDPOINT from_secret., Acceptance: notify-obs has OTEL_HEADERS from_secret., Acceptance: notify-obs has DORA start log at beginning. (+9 more)

### Community 7 - "Legacy Jenkins Library"
Cohesion: 0.25
Nodes (6): 1. Purpose and Scope, 2. Personas and JTBD, 4. Non-Functional Requirements, 5. Acceptance Criteria, 6. Open Questions (block implementation if unresolved), uFawkesPipe — Specification v0.3

### Community 8 - "Woodpecker Config Tests"
Cohesion: 0.05
Nodes (26): Tests for .woodpecker.yml pipeline structure.  Validates step ordering, image pi, Acceptance: secrets-scan uses 'zricethezav/gitleaks:v8.18.2'., Acceptance: secrets-scan command includes '--exit-code=1'., Basic structural validation of .woodpecker.yml., Acceptance: secrets-scan writes JSON report to artifacts/security/., Acceptance: secrets-scan has DORA structured JSON logging., Acceptance: .woodpecker.yml parses as valid YAML., Acceptance: secrets-scan image tag is pinned (not 'latest'). (+18 more)

### Community 9 - "SonarQube Fixtures"
Cohesion: 0.08
Nodes (23): compose_running(), ensure_stack_running(), http_session(), portainer_token(), portainer_url(), Shared fixtures for uFawkesPipe acceptance test suite.  All fixtures here are se, Woodpecker UI URL (open access, HTTP)., SonarQube URL (host-mapped port 9001 → container 9000).      compose.yaml maps 9 (+15 more)

### Community 10 - "Test Fixtures Config"
Cohesion: 0.12
Nodes (19): compose_config(), compose_file(), env_example(), env_example_config(), fawkespipe_config(), fawkespipe_example(), project_root(), Shared test fixtures for all uFawkesPipe test types. (+11 more)

### Community 11 - "Trivy FS Scan Tests"
Cohesion: 0.08
Nodes (13): Acceptance: vuln-scan-fs step (WP-004) is correctly configured., Helper: find the vuln-scan-fs step by name., Acceptance: Step named 'vuln-scan-fs' exists in steps list., Acceptance: vuln-scan-fs uses 'aquasec/trivy:latest'.          Trivy uses :lates, Acceptance: vuln-scan-fs command includes '--format json'., Acceptance: vuln-scan-fs writes to artifacts/security/trivy-repo.json., Acceptance: vuln-scan-fs command includes '--no-progress'., Acceptance: vuln-scan-fs scans current directory ('.'). (+5 more)

### Community 12 - "Stack Health Tests"
Cohesion: 0.09
Nodes (13): Acceptance tests: Stack health verification.  Covers AC-01 through AC-04 (see do, All 4 compose services must report 'running' status., Edge cases: ensure_stack_running behavior., Fixture passes when stack is up.          If the stack is down, pytest.skip is r, Verify all uFawkesPipe services are running and healthy., Woodpecker UI must return HTTP 200 on port 8000., Woodpecker /healthz must return 200 or 204., SonarQube /api/system/status must return status=UP. (+5 more)

### Community 13 - "Pipeline Contract Tests"
Cohesion: 0.09
Nodes (12): Integration tests for pipeline contract and configuration validation., .fawkespipe.yml.example must be valid YAML., .fawkespipe.yml.example must have an app section., .fawkespipe.yml.example must have a build section., .fawkespipe.yml.example must have a stages section., app section must have name, type, language., build section must have a builder field., stages must include lint, test, sast, build, push. (+4 more)

### Community 14 - "Image Signing Tests"
Cohesion: 0.13
Nodes (12): Acceptance: sign-image includes '--yes' flag., Acceptance: sign-image only runs on main branch., Acceptance: sign-image has DORA structured JSON logging., Acceptance: sign-image step is correctly configured., Helper: find the sign-image step by name., Acceptance: Step named 'sign-image' exists in steps list., Acceptance: sign-image uses bitnami/cosign image., Acceptance: sign-image has COSIGN_PRIVATE_KEY from_secret. (+4 more)

### Community 15 - "Trivy Image Scan Tests"
Cohesion: 0.09
Nodes (12): Acceptance: vuln-scan-image step (WP-004) is correctly configured., Helper: find the vuln-scan-image step by name., Acceptance: Step named 'vuln-scan-image' exists in steps list., Acceptance: vuln-scan-image uses 'aquasec/trivy:latest'.          Trivy uses :la, Acceptance: vuln-scan-image command includes '--format json'., Acceptance: vuln-scan-image writes to artifacts/security/trivy-image.json., Acceptance: vuln-scan-image command includes '--no-progress'., Acceptance: vuln-scan-image has when: branch: main condition. (+4 more)

### Community 16 - "SBOM Generation Tests"
Cohesion: 0.09
Nodes (12): Acceptance: generate-sbom step is correctly configured., Helper: find the generate-sbom step by name., Acceptance: Step named 'generate-sbom' exists in steps list., Acceptance: generate-sbom uses 'aquasec/trivy:latest'., Acceptance: generate-sbom has REGISTRY_USERNAME from_secret., Acceptance: generate-sbom produces artifacts/security/sbom.cdx.json., Acceptance: generate-sbom uses CycloneDX format., Acceptance: generate-sbom uses CI built-in variables for image ref. (+4 more)

### Community 17 - "Service Auth Tests"
Cohesion: 0.10
Nodes (13): Acceptance tests: Service authentication.  Covers AC-05 through AC-07 (see docs/, Portainer auth must return a valid JWT.          The portainer_token fixture han, Portainer JWT must grant access to authenticated endpoints., Portainer must respond differently to unauthenticated requests.          Without, Verify Woodpecker is open-access (NO_AUTH mode)., Woodpecker API must respond (even if unauthenticated).          With WOODPECKER_, Verify SonarQube login with default credentials., SonarQube must accept admin/admin login. (+5 more)

### Community 18 - "Suite Behavior Tests"
Cohesion: 0.15
Nodes (13): parse_summary_line(), Acceptance tests: Suite behavior meta-tests.  Covers AC-13 and AC-14 (see docs/a, test_01 health tests must be callable without errors.          This is a basic s, test_03 pipeline structure tests must always collect as expected.          These, Verify AC-14: two consecutive runs produce identical results., Two runs of test_03 must produce identical pass/fail/skip counts., Two runs of test_04 must produce identical pass/fail/skip counts., Run pytest on a specific test file and return (returncode, stdout, stderr). (+5 more)

### Community 19 - "Validate Agents Step"
Cohesion: 0.11
Nodes (10): Acceptance: validate-agents step is correctly configured., Helper: find the validate-agents step by name., Acceptance: Step named 'validate-agents' exists in steps list., Acceptance: validate-agents uses 'alpine:3.20'., Acceptance: validate-agents depends on init step., Acceptance: validate-agents installs bash via apk., Acceptance: validate-agents calls scripts/validate-agents.sh., Acceptance: validate-agents has DORA structured JSON logging. (+2 more)

### Community 20 - "Dependency Automation"
Cohesion: 0.12
Nodes (15): assignees, automerge, extends, github-actions, enabled, fileMatch, labels, packageRules (+7 more)

### Community 21 - "Artifact Init Tests"
Cohesion: 0.12
Nodes (9): Automated acceptance test for WP-001: Add artifact directory init step to .woodp, Validate WP-001 artifact directory initialization., Load and parse .woodpecker.yml, Acceptance: .woodpecker.yml first step is named 'init', image 'alpine:3.20, Acceptance: init commands include 'mkdir -p artifacts/security, Acceptance: init commands include 'mkdir -p artifacts/coverage, Acceptance: init commands include 'mkdir -p artifacts/tests, Acceptance: init uses 'mkdir -p' for idempotent directory creation (+1 more)

### Community 22 - "Gitleaks Secrets Scan"
Cohesion: 0.40
Nodes (5): 3.1 Compose Lifecycle Fixtures, 3.2 HTTP Helper Fixtures, 3.3 Authentication Token Fixtures, 3.4 Pipeline Configuration Fixtures, 3. Shared Fixtures (`conftest.py`)

### Community 23 - "Portainer CD Tests"
Cohesion: 0.14
Nodes (9): Acceptance tests: Portainer CD readiness.  Covers AC-11 (see docs/acceptance-cri, Portainer webhooks endpoint must return HTTP 200.          GET /api/webhooks ret, Verify Portainer is configured and ready for CD operations., Portainer GET /api/endpoints must return HTTP 200.          The response may be, Portainer must have Docker access (socket mounted).          If an endpoint exis, Portainer CD readiness: full auth + API workflow.          Verifies the complete, Verify Portainer exposes webhook endpoint for CD., TestPortainerCDReadiness (+1 more)

### Community 24 - "Compose Integration"
Cohesion: 0.17
Nodes (7): Integration tests for Docker Compose configuration validation., compose.yaml must have services section with expected services., All core services should have healthchecks., No service should use :latest image tags., Top-level volumes should be named volumes., Cross-component validation of Docker Compose configuration., TestComposeIntegration

### Community 25 - "Full Pipeline E2E"
Cohesion: 0.17
Nodes (7): DEPRECATED — Acceptance tests for pipeline structure.  This file is kept for ref, End-to-end pipeline validation (deprecated — see test_03_*)., .woodpecker.yml must have the expected 6-stage ordering., Pipeline steps must have correct dependency ordering., .woodpecker.yml must have a global when condition., yamllint must pass on key YAML files., TestFullPipeline

### Community 26 - "SonarQube Health"
Cohesion: 0.20
Nodes (6): Smoke tests for SonarQube health verification., Check if compose stack is running., SonarQube /api/system/status must return UP., SonarQube UI must be accessible., Verify SonarQube is running and healthy., TestSonarQubeHealth

### Community 27 - "Woodpecker Health"
Cohesion: 0.20
Nodes (6): Smoke tests for Woodpecker CI health verification., Check if compose stack is running., Woodpecker /healthz endpoint must return 200., Woodpecker UI must be accessible., Verify Woodpecker CI is running and healthy., TestWoodpeckerHealth

### Community 28 - "Language Contracts"
Cohesion: 0.42
Nodes (9): Go Service Pipeline Contract, Java Spring Boot Maven Pipeline Contract, Node.js Express Pipeline Contract, Python Flask Pipeline Contract, uFawkesPipe Pipeline Contract, Tests Python Dependencies, pytest >=8.0, PyYAML >=6.0 (+1 more)

### Community 29 - "SonarQube Simulation"
Cohesion: 0.29
Nodes (5): Acceptance tests: Security tool simulation.  Covers AC-10 (see docs/acceptance-c, Verify SonarQube project create/search/delete (SAST simulation).      Each test, Helper: delete the test project (no-op if not found)., SonarQube must accept project creation and return correct key., TestSonarQubeProjectLifecycle

### Community 30 - "DORA Log Script"
Cohesion: 0.43
Nodes (7): dora_emit(), dora_end(), dora_error(), dora_info(), dora_start(), dora_warn(), dora-log.sh script

### Community 31 - "Contributing & Policy"
Cohesion: 0.18
Nodes (11): Attribution, Contributor Covenant Code of Conduct, Enforcement, Our Pledge, Our Standards, Contributing Guide, Conventional Commits, healthcheck Required on All Services (+3 more)

### Community 32 - "Pre-flight Validation"
Cohesion: 0.70
Nodes (4): validate.sh script, error(), success(), warning()

### Community 33 - "CI Diagnosis & Fix"
Cohesion: 0.40
Nodes (5): 6. Tradeoffs and Decisions, Decision 1: pytest over Gherkin/BDD, Decision 2: No Selenium/Browser Automation, Decision 3: Portainer Admin Initialization Strategy, Decision 4: Pipeline Structure via File Parsing, Not API

### Community 46 - "Community 46"
Cohesion: 0.12
Nodes (15): 1. GitHub Webhooks, 2. Woodpecker REST API, 3. Woodpecker CLI, 4. Portainer Webhook (CD), Authentication, Base URL, Build Status API, Common Endpoints (+7 more)

### Community 47 - "Community 47"
Cohesion: 0.05
Nodes (37): Acceptance criteria, Acceptance criteria, Acceptance criteria, Acceptance criteria, Acceptance criteria, Acceptance criteria, Acceptance criteria, Acceptance criteria (+29 more)

### Community 48 - "Community 48"
Cohesion: 0.05
Nodes (43): 📚 Additional Resources, 🏗️ Architecture, CLI Commands, 🔧 Configuration, Container Security, 🤝 Contributing, DefectDojo Integration, Dependency Scanning (+35 more)

### Community 49 - "Community 49"
Cohesion: 0.07
Nodes (30): 10. Test Architecture, 11. File Reference Map, 12.1 Standalone Mode (default), 12.2 Suite Mode, 12.3 What Changes in Suite Mode, 12.4 Telemetry Architecture, 12. Suite Mode Architecture, 1. System Overview (+22 more)

### Community 50 - "Community 50"
Cohesion: 0.09
Nodes (22): 10. Suite Integration, 1. Identity, 2. Where the Agents Live, 3. Context Files — Read Before Generating Anything, 4. Architecture Rules — Never Violate These, 5. The PM–Agent Contract, 6. TDD Commit Order, 7. AI-Assisted Review Block (+14 more)

### Community 51 - "Community 51"
Cohesion: 0.08
Nodes (23): advanced — Advanced Configuration, app — Application Metadata, build — Build Configuration, build (stage), CNB Builder, Complete Example, dependency_scan, Docker Builder (+15 more)

### Community 52 - "Community 52"
Cohesion: 0.17
Nodes (12): 1. Architecture Overview, 2. Component Map, 4.1 Test-to-Service Interactions, 4.2 Error Handling Contract, 4.3 Skip Contract, 4. Interface Definitions, 5. Data Flow, 7. Impacted Files (+4 more)

### Community 53 - "Community 53"
Cohesion: 0.10
Nodes (20): Change Failure Rate, Change Failure Rate, Deployment Events, Deployment Frequency, Deployment Frequency (per day), DORA Metrics Collection, Grafana Dashboard, Lead Time for Changes (+12 more)

### Community 54 - "Community 54"
Cohesion: 0.07
Nodes (29): 1. Add `.fawkespipe.yml` to your repository, 2. Enable the repository in Woodpecker, 3. Push code, 4. Monitor the pipeline, Common Commands, Configuration, Core Variables, Create Your First Pipeline (+21 more)

### Community 56 - "Community 56"
Cohesion: 0.11
Nodes (18): AC-01: Stack Health — All Services Accessible, AC-02: Woodpecker Health Verification, AC-03: SonarQube Health Verification, AC-04: Portainer Health Verification, AC-05: Woodpecker Open Access Verification, AC-06: SonarQube Authentication, AC-07: Portainer First-Run Initialization + Authentication, AC-08: Woodpecker Pipeline Structure Verification (+10 more)

### Community 57 - "Community 57"
Cohesion: 0.11
Nodes (17): [0.1.0] - 2026-06-01, [0.2.0] - 2026-06-15, [0.3.0] - 2026-06-30, Added, Added, Added, Added, Changed (+9 more)

### Community 58 - "Community 58"
Cohesion: 0.25
Nodes (7): Date of Migration, How to Access Historical Jenkins Pipeline Runs, Jenkins → Woodpecker CI Migration, New Stack Quick Reference, See Also, What Was Replaced, Why

### Community 59 - "Community 59"
Cohesion: 0.12
Nodes (15): Code Conventions, Code of Conduct, Commit Messages, Contributing to uFawkesPipe, Development Setup, Docker Compose, Exception: Vulnerability Scanner Images, License (+7 more)

### Community 61 - "Community 61"
Cohesion: 0.25
Nodes (8): 3.1 Stack Health Verification, 3.2 Authentication Verification, 3.3 Golden Path Pipeline Simulation, 3.4 Security Verification, 3.5 Deployment & Observability, 3.6 Test Infrastructure, 3.7 Documentation, 3. Functional Requirements — v0.3 Acceptance Test Suite

### Community 67 - "Community 67"
Cohesion: 0.33
Nodes (5): Cost Tracking, Current Model Assignment, Mode Selection, Model Policy — uFawkesPipe, When to Change Model

### Community 68 - "Community 68"
Cohesion: 0.17
Nodes (12): Exceptions, Golden Path Cheat Sheet, Golden Path — uFawkesPipe, Phase 0 — Discovery & Spec, Phase 1 — Design, Phase 2 — Plan, Phase 3 — Build, Phase 4 — Test Execution (+4 more)

### Community 69 - "Community 69"
Cohesion: 0.07
Nodes (30): Agent Context Shared State, Rename Plan deliveryd to uFawkesPipe, buildImage.groovy, loadConfig.groovy, promoteToProduction.groovy, seed-job.groovy, ufawkes-cli, Architecture Rules (+22 more)

### Community 70 - "Community 70"
Cohesion: 0.22
Nodes (8): Acceptance Criterion, Discovery Brief: Automated Acceptance Test Suite, DORA Outcome Target, Golden Path (build → scan → deploy), Job to Be Done, Notes, Prior Art, Riskiest Assumption

### Community 71 - "Community 71"
Cohesion: 0.20
Nodes (9): Credential Handling, DORA Logging — Strict Rules, Error Handling, File Convention, Idempotency Patterns, Pattern 1: Marker File (preferred), Pattern 2: Check Output, Pipeline Library — Woodpecker CI Standards (+1 more)

### Community 74 - "Community 74"
Cohesion: 0.22
Nodes (8): Actual Behavior, Additional Context, Bug Description, Environment, Expected Behavior, Logs, Make Up Output, Steps to Reproduce

### Community 75 - "Community 75"
Cohesion: 0.22
Nodes (8): Acceptance Criteria (Phase E), E1: Implement `shared/vars/loadConfig.groovy`, E2: Implement `shared/vars/buildImage.groovy`, E3: Implement Real Seed Job, E4: Implement Environment Promotion, E5: Implement `ufawkes-cli` Self-Service Tool, Phase E: Platform Implementation (from 0.1% review), Rename Plan: deliveryd → uFawkesPipe

### Community 76 - "Community 76"
Cohesion: 0.22
Nodes (8): Anti-Patterns, DORA Metrics, DORA Metrics Log Format — Single Source of Truth, Error Events (on failure), Format Specification, Groovy Utility, Log Line Examples, Stage Events

### Community 79 - "Community 79"
Cohesion: 0.25
Nodes (7): Changed Files, CI Fix Report — PR #55 `feat/gitops-lifecycle-gates`, Remaining Risks, Root Cause Details, Summary, Validation, What Changed

### Community 80 - "Community 80"
Cohesion: 0.25
Nodes (7): Breaking Change Rules, Contract File, Deprecation Shim (in Woodpecker / GitHub Actions), Migration Checklist When Contract Changes, Pipeline Contract — Schema and Migration, Schema Reference, Validation

### Community 83 - "Community 83"
Cohesion: 0.29
Nodes (6): Additional Context, Alternatives Considered, DORA Capability Impact, Implementation Notes, Problem Statement, Proposed Solution

### Community 84 - "Community 84"
Cohesion: 0.29
Nodes (6): Adding a New Language, Example Pipeline Contract Pattern (.fawkespipe.yml — app teams create this), Language Pack — Buildpack Language Support, Pack Directory Structure, Validation Checklist for New Packs, Woodpecker Pipeline Template (Current)

### Community 86 - "Community 86"
Cohesion: 0.33
Nodes (5): CI Diagnosis — PR #55 `feat/gitops-lifecycle-gates`, Failure 1, 2, 3: Markdown Lint Failure, Failure 4: Pipeline Complete (Cascade), Failure Summary, Individual Diagnoses

### Community 88 - "Community 88"
Cohesion: 0.33
Nodes (5): Active Task, Agent Context — Shared State, Agent Health, Notes, Recent Changes

### Community 92 - "Community 92"
Cohesion: 0.40
Nodes (4): 1. Impacted Components, 2. Change Details, 3. Anti-Goals, PIPE-004 — Design: Fix Stale File Reference in workflow-agent.md

### Community 94 - "Community 94"
Cohesion: 0.40
Nodes (4): 1. Problem, 2. Requirements, 3. Acceptance Criteria, PIPE-004 — Fix Stale File Reference in workflow-agent.md

## Knowledge Gaps
- **395 isolated node(s):** `1. Identity`, `2. Where the Agents Live`, `3. Context Files — Read Before Generating Anything`, `compose.yaml`, `Woodpecker Configuration (`.woodpecker.yml`)` (+390 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DORA Logging Anchor` connect `Platform Architecture` to `Community 46`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **Why does `uFawkesPipe — Architecture` connect `Community 49` to `Platform Architecture`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **Why does `uFawkesPipe — Implementation Plan v0.2` connect `Community 47` to `Platform Architecture`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `DORA Logging Anchor` (e.g. with `Reusable Lint Workflow` and `Reusable Main CI Guard Workflow`) actually correct?**
  _`DORA Logging Anchor` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Shared fixtures for uFawkesPipe acceptance test suite.  All fixtures here are se`, `Skip test if compose stack is not running.      Tests that require a running sta`, `Check that all 4 compose services are running.      Session-scoped — checked onc` to the rest of the system?**
  _661 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Platform Architecture` be split into smaller, more focused modules?**
  _Cohesion score 0.05870020964360587 - nodes in this community are weakly interconnected._
- **Should `Pipeline Structure Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._