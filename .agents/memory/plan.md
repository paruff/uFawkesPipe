# Rename Plan: deliveryd → uFawkesPipe

> **Status:** Completed (Phases A-D)
> **Owner:** Agent team
> **Migration strategy:** In-place rename across 25 files, staged by risk category
> **Pipeline contract note:** `.deliveryd.yml` is renamed to `.fawkespipe.yml` — this is a **breaking change** for all consuming app teams. One-week deprecation period with both files supported.

---

## Phase E: Platform Implementation (from 0.1% review)

> These 5 items were identified by a 0.1% platform engineering review as the gap between the current proof-of-concept and a production-ready Internal Developer Platform.

### E1: Implement `shared/vars/loadConfig.groovy`

**Priority:** Critical
**Why:** The pipeline contract parser is the core of the platform. Without it, the `.fawkespipe.yml` contract is just a spec.

```
shared/vars/loadConfig.groovy
├── Read .fawkespipe.yml (with deprecation shim for .deliveryd.yml)
├── Validate required fields (app.name, app.type, app.language)
├── Apply defaults for optional fields
├── Return typed config map
├── DORA logging: start, SHA, finish
└── Idempotent: safe to re-run
```

### E2: Implement `shared/vars/buildImage.groovy`

**Priority:** Critical
**Why:** The build step is the core value of the platform. Must support both CNB and Docker builders.

```
shared/vars/buildImage.groovy
├── Accept config map from loadConfig()
├── Support builder: cnb | docker
├── CNB: invoke pack CLI with builder, buildpacks, env vars
├── Docker: invoke docker build with Dockerfile, context, target, buildArgs
├── Tag strategy: ${GIT_COMMIT_SHORT}, ${GIT_BRANCH}, ${APP_NAME}
├── Archive build metadata as artifacts
├── DORA logging: start, SHA, finish
└── Idempotent: safe to re-run
```

### E3: Implement Real Seed Job

**Priority:** High
**Why:** The seed job is a placeholder. Real platform engineering needs dynamic pipeline creation from `.fawkespipe.yml` repos.

```
jenkins/seed-job.groovy
├── Scan configured GitHub org/repos for .fawkespipe.yml
├── Create/update pipeline jobs dynamically
├── Set job parameters from contract (language, builder, stages)
├── Configure webhooks automatically
├── Remove stale jobs for deleted repos
├── Log: repos scanned, jobs created, jobs removed
└── Run on schedule (daily) + manual trigger
```

### E4: Implement Environment Promotion

**Priority:** High
**Why:** Pipeline deploys to K8s but there's no staging → production promotion logic, no canary, no rollback.

```
shared/vars/promoteToProduction.groovy
├── Accept: image tag, source namespace, target namespace
├── Gate: require manual approval (Jenkins approval step)
├── Canary: deploy to 10% traffic, monitor for 5 minutes
├── Promote: full rollout if canary passes
├── Rollback: automatic if health check fails
├── Notify: Slack/email on success/failure
├── DORA logging: start, SHA, finish
└── Idempotent: safe to re-run
```

### E5: Implement `ufawkes-cli` Self-Service Tool

**Priority:** Medium
**Why:** App teams can't onboard without platform team help. A real IDP has a CLI for self-service.

```
scripts/ufawkes-cli
├── Commands:
│   ├── onboard    — Create .fawkespipe.yml from template
│   ├── validate   — Lint contract against schema
│   ├── status     — Show pipeline status for a repo
│   ├── logs       — Fetch build logs
│   └── promote    — Trigger promotion to production
├── Language detection: auto-detect from repo structure
├── Template engine: generate contract from language preset
├── Output: colored, machine-readable (JSON optional)
└── Install: curl | bash or brew
```

---

## Acceptance Criteria (Phase E)

- [ ] `shared/vars/loadConfig.groovy` parses `.fawkespipe.yml` and returns typed config
- [ ] `shared/vars/buildImage.groovy` builds images via both CNB and Docker
- [ ] Seed job scans repos and creates pipeline jobs dynamically
- [ ] Environment promotion works: staging → canary → production
- [ ] `ufawkes-cli onboard` generates valid `.fawkespipe.yml` for a new repo
- [ ] All shared library steps have DORA logging
- [ ] All shared library steps are idempotent
- [ ] Integration test: full pipeline run on a sample repo
