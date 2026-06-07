# Rename Plan: deliveryd → uFawkesPipe

> **Status:** Planned
> **Owner:** Agent team
> **Migration strategy:** In-place rename across 25 files, staged by risk category
> **Pipeline contract note:** `.deliveryd.yml` is renamed to `.fawkespipe.yml` — this is a **breaking change** for all consuming app teams. One-week deprecation period with both files supported.

---

## Scope (25 files, ~320 references)

| Category | Files | Change Type | Risk |
|---|---|---|---|
| **Identity & Headers** (6) | `AGENTS.md`, `README.md`, `QUICKSTART.md`, `docs/CHANGE_IMPACT_MAP.md`, `validate.sh`, `.github/instructions/jenkinsfile.instructions.md` | Project name, description, system message | Low |
| **Docker metadata** (2) | `docker-compose.yml`, `Dockerfile` | Container names, network names, volume names, image refs | Medium |
| **Jenkins config** (2) | `jenkins/casc.yaml`, `Jenkinsfile` | Library names, URLs, system messages, folder names, credential IDs | High |
| **K8s manifests** (6) | `k8s/*.yaml`, `k8s/README.md` | Namespace, labels, image refs, documentation | Medium |
| **Pipeline contract** (5) | `.deliveryd.yml.example`, `examples/*.yml` | **Breaking**: filename change + internal references | **Critical** |
| **Makefile** (1) | `Makefile` | Volume names, backup paths, messages | Low |
| **Environment** (1) | `.env.example` | Comments, namespace defaults | Low |
| **Validation** (1) | `validate.sh` | File paths, messages | Low |
| **Documentation** (3) | `docs/webhook-api.md`, `docs/kubernetes-promotion.md`, `QuICKSTART.md` | URLs, namespace references, examples | Low |

---

## Migration Order (4 phases)

### Phase A: Identity & Metadata (low risk, high visibility)

Files: `AGENTS.md`, `README.md`, `validate.sh`, `Makefile`, `.env.example`

```
Replacements:
  "deliveryd" (project name)    → "uFawkesPipe"
  "deliveryd" (system)          → "uFawkesPipe Integration Plane"
  "Integration & Delivery Plane" → "Integration & Delivery Plane of Fawkes IDP"
  github.com/paruff/deliveryd   → github.com/paruff/uFawkesPipe
```

### Phase B: Platform Configuration (medium risk)

Files: `docker-compose.yml`, `jenkins/Dockerfile`, `jenkins/casc.yaml`, `Jenkinsfile`

```
Replacements:
  container_name: deliveryd-*       → container_name: ufp-*
  network: deliveryd-network        → network: ufp-network
  volume: deliveryd_*               → volume: ufp_*
  @Library('deliveryd-*')           → @Library('ufawkespipe-*')
  "deliveryd-pipeline-library"      → "ufawkespipe-pipeline-library"
  remote: "*/deliveryd"             → remote: "*/uFawkesPipe"
  credentialsId: "deliveryd-*"      → credentialsId: "ufp-*"
  deliveryd/jenkins:latest          → ufawkespipe/jenkins:latest
```

### Phase C: Kubernetes Manifests (medium risk)

Files: `k8s/*.yaml`, `k8s/README.md`

```
Replacements:
  namespace: deliveryd           → namespace: ufawkespipe
  deliveryd/jenkins:latest       → ufawkespipe/jenkins:latest
  your-registry/deliveryd-*      → your-registry/ufp-*
  app: deliveryd                 → app: ufawkespipe
  plane: deliveryd               → plane: ufawkespipe
```

### Phase D: Pipeline Contract — BREAKING (critical)

Files: `.deliveryd.yml.example`, `examples/.deliveryd-*.yml`, `docs/CHANGE_IMPACT_MAP.md`

```
Renames:
  .deliveryd.yml.example                → .fawkespipe.yml.example
  examples/.deliveryd-java-maven.yml    → examples/.fawkespipe-java-maven.yml
  examples/.deliveryd-python-flask.yml  → examples/.fawkespipe-python-flask.yml
  examples/.deliveryd-nodejs-express.yml → examples/.fawkespipe-nodejs-express.yml
  examples/.deliveryd-go.yml            → examples/.fawkespipe-go.yml

Internal:
  .deliveryd.yml   → .fawkespipe.yml  (all code/docs references)
  deliveryd Pipeline Contract → uFawkesPipe Pipeline Contract
```

All `Jenkinsfile` logic that reads `.deliveryd.yml` must be updated to:
```groovy
// Deprecation shim: support both filenames during migration
def contractFile = fileExists('.fawkespipe.yml') ? '.fawkespipe.yml' : '.deliveryd.yml'
CONFIG = readYaml file: contractFile
```

---

## Rollback Strategy

Each phase is a separate PR. If Phase D causes issues:
1. Revert the single PR
2. Restore `.deliveryd.yml.example` as a symlink to `.fawkespipe.yml.example`
3. Keep the shim in `Jenkinsfile` for 1 week

---

## Acceptance Criteria

- [ ] All 25 files updated with zero `deliveryd` references (excluding git history)
- [ ] `grep -rn "deliveryd" --include="*.yml" --include="*.yaml" --include="*.md" --include="*.sh" --include="Makefile" --include="*.groovy" --include="Jenkinsfile" --include="*.txt" . | grep -v ".git/"` returns empty
- [ ] Pipeline still functions: `make validate` passes
- [ ] Jenkins seed job creates pipelines under new naming
- [ ] K8s manifests apply cleanly with new namespace
- [ ] `examples/*.fawkespipe-*.yml` files parse correctly
- [ ] Cross-plane references in docs updated (Obstackd, developerd, fawkes)
