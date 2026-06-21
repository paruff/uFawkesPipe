# Jenkins → Woodpecker CI Migration

## What Was Replaced

**Jenkins** (CI/CD orchestrator) → **Woodpecker CI** (pipeline engine) + **Portainer CE** (deployment management)

| Component | Pre-migration | Post-migration |
|-----------|--------------|----------------|
| Pipeline engine | Jenkins Master (v2.492.x) | Woodpecker Server + Agent (v3.15.0) |
| Pipeline definition | Jenkinsfile (Groovy/Jenkins DSL) | `.woodpecker.yml` (YAML) |
| Configuration as code | JCasC YAML (`jenkins/casc.yaml`) | Woodpecker UI + environment variables |
| Deployment/CD | Jenkins pipeline stages | Portainer CE (Docker management UI) |
| Service orchestration | `docker-compose.yml` | `compose.yaml` |
| Plugin management | `jenkins/plugins.txt` | Not applicable (Woodpecker built-in) |
| Shared libraries | `shared/vars/*.groovy` | Woodpecker pipeline workflows |

## Why

1. **Resource footprint** — Jenkins requires 2-4 GB RAM, persistent volumes, and multiple plugins that each consume memory. Woodpecker Server + Agent runs in ~200 MB.
2. **Groovy complexity** — Jenkins pipeline syntax (Groovy DSL) is difficult to test, debug, and maintain. Woodpecker uses simple YAML pipeline definitions that are easy to read and validate.
3. **IDP standardisation** — The Fawkes IDP family standardises on Woodpecker CI across all planes. uFawkesObs, uFawkesSec, and fawkes all use Woodpecker-compatible pipelines. Maintaining a separate Jenkins stack increased cognitive load for platform engineers.
4. **Plugin fragility** — Jenkins plugin compatibility matrix required careful version management. Woodpecker's built-in features (Docker, GitHub, CLI triggers) cover the same use cases without plugin management overhead.
5. **Startup time** — Jenkins takes 2-3 minutes to start (loading plugins, JCasC, jobs). Woodpecker starts in <10 seconds.

## Date of Migration

**June 2026** — uFawkesPipe migrated from Jenkins to Woodpecker CI + Portainer CD as part of the PIPE-01 feature set.

| Migration Step | Date | Commit |
|----------------|------|--------|
| LICENSE change (MIT → Apache 2.0) | Jun 2026 | `PIPE-01-01` |
| `compose.yaml` created with Woodpecker/Portainer/SonarQube | Jun 2026 | `PIPE-01-02` |
| `.env.example` updated for Woodpecker | Jun 2026 | `PIPE-01-03` |
| `.woodpecker.yml` pipeline created | Jun 2026 | `PIPE-01-04` |
| Test suite migrated from Jenkins to woodpecker-validated | Jun 2026 | `PIPE-01-05` |
| Jenkins artifacts archived | Jun 2026 | `PIPE-01-06` |

## How to Access Historical Jenkins Pipeline Runs

The Jenkinsfile and Jenkins configuration are preserved in this repository for historical reference:

- **Archived Jenkinsfile**: `docs/history/Jenkinsfile.archived` — Contains the full Groovy pipeline definition including all stages (lint, test, SAST, build, scan, push, deploy).
- **Archived Jenkins configuration**: `docs/history/jenkins/` — Contains `casc.yaml` (JCasC), `Dockerfile` (JNLP agent), and `plugins.txt` (plugin list).

To view the Jenkins-era pipeline definition at any point in git history:

```bash
# View the Jenkinsfile as it existed before archival
git show HEAD~1:Jenkinsfile

# View the Jenkins configuration directory
git show HEAD~1:jenkins/casc.yaml
git show HEAD~1:jenkins/plugins.txt
git show HEAD~1:jenkins/Dockerfile

# View all commits that modified the Jenkinsfile
git log --oneline -- Jenkinsfile
```

For users migrating from earlier versions of uFawkesPipe that depended on Jenkins:

1. The `.fawkespipe.yml` pipeline contract file is **still supported** — Woodpecker reads the same configuration fields.
2. The `shared/` directory Groovy library has been replaced by Woodpecker pipeline workflows.
3. The `k8s/` Kubernetes manifests remain valid for running uFawkesPipe components on Kubernetes.

## New Stack Quick Reference

```bash
# Start the new stack
make up

# Access Woodpecker CI
open http://localhost:8000

# Access Portainer CD
open https://localhost:9443

# Access SonarQube
open http://localhost:9001
```

## See Also

- [`compose.yaml`](../../compose.yaml) — Current service stack definition
- [`.woodpecker.yml`](../../.woodpecker.yml) — Current pipeline definition
- [`.env.example`](../../.env.example) — Required environment variables
- [`Makefile`](../../Makefile) — `make up`, `make down`, `make status` targets
