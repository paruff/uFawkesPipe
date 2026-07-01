# WP-008 — Design: Update README and Add docs/pipeline-contract.md

## 1. Impacted Components

| Component | File | Change |
|---|---|---|
| Project README | `README.md` | Full rewrite for v0.2 accuracy |
| Pipeline Contract Doc | `docs/pipeline-contract.md` | New file — authoritative contract reference |
| Makefile targets | `Makefile` | Reference only (no changes) |
| Pipeline contract example | `.fawkespipe.yml.example` | Reference for examples |
| Language examples | `examples/` | Reference for language-specific configs |

---

## 2. Document Structure Redesign

### 2.1 README.md New Section Organization

```
# uFawkesPipe

## 🚀 Features (updated)
## 📋 Pipeline Stages (updated — match .woodpecker.yml)
## 🏗️ Architecture (updated — remove k8s/, add suite mode)
## 🛠️ Quick Start (updated — standalone + suite)
## 📖 Pipeline Contract Reference (updated — link to docs/pipeline-contract.md)
## 🔌 Webhook API (updated)
## ☸️ Kubernetes Promotion Path (updated — remove k8s/ refs, note future)
## 🔒 Security Features (updated — match pipeline steps)
## 🔧 Configuration (updated)
## 🐛 Troubleshooting (updated — v0.2 stack)
## 📚 Additional Resources (unchanged)
## 🤝 Contributing (unchanged)
## 📄 License (unchanged)
## 🙋 Support (unchanged)
## uFawkes Stack Ecosystem (updated — verify links)
```

### 2.2 docs/pipeline-contract.md Structure

```
# Pipeline Contract Reference — .fawkespipe.yml

## Overview
## app — Application Metadata
## build — Build Configuration
  - builder: cnb | docker | custom
  - cnb — CNB-specific options
  - docker — Docker-specific options
  - image — Image registry/name/tag strategy
## stages — Pipeline Stages Configuration
  - lint
  - test
  - sast
  - dependency_scan
  - build
  - image_scan
  - push
## notifications — Notifications
## kubernetes — Kubernetes Deployment (promotion path)
## advanced — Advanced Configuration
## Complete Example
## Language-Specific Examples (links to examples/)
```

---

## 3. Detailed Content Specification

### 3.1 README.md Key Changes

| Old Content | New Content |
|---|---|
| Pipeline Stages: 8 generic stages (Lint, Unit Tests, SAST, Dependency Scan, Build, Image Scan, Push, Deploy) | Pipeline Steps matching `.woodpecker.yml`: init, secrets-scan, lint-yaml, lint-shell, validate-pipeline-contract, vuln-scan-fs, vuln-scan-image, upload-defectdojo, notify-obs |
| Service Access: SonarQube on 9001 | SonarQube on 9000 (matches compose.yaml) |
| Installation: `make up` only | `make up` (standalone) + `make up-suite` (suite mode) |
| Kubernetes Promotion: references `k8s/` manifests | Note: k8s/ removed; promotion path TBD for Woodpecker |
| Pipeline Contract: brief section | Full section linking to `docs/pipeline-contract.md` |
| Architecture diagram: shows Jenkins | Architecture: Woodpecker + SonarQube + Portainer + CNB |
| Troubleshooting: Jenkins-focused | Woodpecker, SonarQube, OTEL, pack, ports |

### 3.2 docs/pipeline-contract.md Content

Each section from `.fawkespipe.yml.example` gets:
- Field table (name, type, required, default, description)
- Valid values / constraints
- Example snippet
- Cross-references to language-specific examples in `examples/`

---

## 4. File Mapping

| Source | Lines | Action |
|---|---|---|
| `README.md` | 1-435 | Full rewrite |
| `.fawkespipe.yml.example` | 1-170 | Primary source for contract doc |
| `examples/*` | — | Reference for language examples |
| `.woodpecker.yml` | 1-177 | Source for pipeline steps |
| `compose.yaml` | — | Source for service ports |
| `Makefile` | — | Source for command reference |
| `QUICKSTART.md` | — | Consistency reference |

---

## 5. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Port mismatch (SonarQube 9000 vs 9001) | Low | Verify against compose.yaml |
| Broken links to deleted k8s/ | Medium | Search and replace all k8s/ references |
| Pipeline steps out of sync with .woodpecker.yml | Medium | Copy directly from .woodpecker.yml |
| Missing env var in docs | Low | Cross-reference with .env.example |
| Contract doc drift from .fawkespipe.yml.example | Medium | Single-source-from-example pattern |
