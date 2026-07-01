# WP-008 — Update README and Add docs/pipeline-contract.md

**Type:** docs / feat
**Depends on:** WP-001 (init), WP-004 (vuln-scan-fs), WP-005 (upload-defectdojo), WP-006 (notify-obs), WP-007 (QUICKSTART v0.2)
**Branch:** `feature/wp-008-readme-pipeline-contract`

---

## 1. Problem

The current `README.md` documents the v0.2 stack partially but contains several stale references and gaps:
- References `k8s/` directory for Kubernetes manifests (deleted in WP-007)
- References legacy `docker-compose.yml` instead of `compose.yaml`
- SonarQube port listed as 9001 (should be 9000)
- Pipeline stages list includes 8 stages but `.woodpecker.yml` has different steps
- No reference to the new `.fawkespipe.yml` pipeline contract format (v0.2)
- Missing documentation of Woodpecker CI steps (secrets-scan, validate-pipeline-contract, vuln-scan-fs/image, upload-defectdojo, notify-obs)
- Missing suite mode documentation
- No link to `docs/pipeline-contract.md` (which doesn't exist yet)

A dedicated `docs/pipeline-contract.md` is needed to serve as the authoritative reference for the `.fawkespipe.yml` contract — currently only `.fawkespipe.yml.example` exists with inline comments.

---

## 2. Requirements

### Functional

| # | Requirement | Rationale |
|---|---|---|
| F1 | Rewrite README.md to accurately reflect v0.2 Woodpecker CI + CNB stack | Accurate project landing page |
| F2 | Remove all `k8s/` references (directory deleted) | Prevent broken links |
| F3 | Update SonarQube port from 9001 → 9000 | Match compose.yaml |
| F4 | Document actual `.woodpecker.yml` pipeline steps | Developer discoverability |
| F5 | Document `.fawkespipe.yml` contract structure and link to new docs/pipeline-contract.md | Contract discoverability |
| F6 | Create `docs/pipeline-contract.md` as authoritative contract reference | Single source of truth for contract |
| F7 | Document standalone mode (`make up`) and suite mode (`make up-suite`) | Both deployment modes |
| F8 | Update troubleshooting for v0.2 stack | Help users resolve issues |
| F9 | Update uFawkes Stack Ecosystem table | Accurate cross-repo links |

### Non-Functional

| # | Requirement | Rationale |
|---|---|---|
| NF1 | Follow existing markdown style (headers, code blocks, tables) | Consistency with repo docs |
| NF2 | No hardcoded secrets — use `your_` placeholder convention | Security compliance |
| NF3 | All internal links must resolve | Documentation quality |
| NF4 | Pass `markdownlint` and `pre-commit run --all-files` | CI gate compliance |

---

## 3. Acceptance Criteria

1. **README.md** — Prerequisites: Docker 20.10+, Docker Compose v2, 4GB+ RAM, GitHub OAuth, DockerHub account
2. **README.md** — Installation: `make up` (standalone) and `make up-suite` (suite mode with deps)
3. **README.md** — Service Access table: Woodpecker (8000), Portainer (9443), SonarQube (9000) — **port 9000**
4. **README.md** — Pipeline Stages section matches actual `.woodpecker.yml` steps (init, secrets-scan, lint-yaml, lint-shell, validate-pipeline-contract, vuln-scan-fs, vuln-scan-image, upload-defectdojo, notify-obs)
5. **README.md** — Pipeline Contract section references `.fawkespipe.yml` and links to `docs/pipeline-contract.md`
6. **README.md** — No references to `k8s/` directory or legacy `docker-compose.yml`
7. **README.md** — Language-specific examples reference `examples/` directory
8. **README.md** — Troubleshooting covers Woodpecker, SonarQube, OTEL, pack, port conflicts
9. **README.md** — uFawkes Stack Ecosystem table has correct links
10. **docs/pipeline-contract.md** — Exists and documents all sections of `.fawkespipe.yml`: app, build, stages, notifications, kubernetes, advanced
11. **docs/pipeline-contract.md** — Includes field descriptions, valid values, examples for each section
12. **docs/pipeline-contract.md** — Links to `.fawkespipe.yml.example` and `examples/` language-specific files
13. All markdown passes `markdownlint` and `pre-commit run --all-files`

---

## 4. Dependencies

- **WP-001** (init): Artifact directories exist for pipeline validation
- **WP-004** (vuln-scan-fs): Documented in pipeline steps
- **WP-005** (upload-defectdojo): Documented in pipeline steps
- **WP-006** (notify-obs): Documented in pipeline steps
- **WP-007** (QUICKSTART v0.2): Consistent terminology and commands

---

## 5. Out of Scope

- Full `QUICKSTART.md` rewrite (done in WP-007)
- `docs/ARCHITECTURE.md` updates
- `docs/KNOWN_LIMITATIONS.md` updates
- Migration guide for Jenkins → Woodpecker
