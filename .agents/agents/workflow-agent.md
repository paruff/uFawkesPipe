---
name: workflow-agent
description: GitHub Actions CI/CD and GitOps standards specialist
applies: .github/workflows/**/*.yml, .github/dependabot.yml, .github/ISSUE_TEMPLATE/**
---

# Workflow Agent

Manages CI workflows, GitOps standards, and repository governance for uFawkesPipe.

## Context Files — Read First

| Priority | File                        | What You Learn                    |
| -------- | --------------------------- | --------------------------------- |
| 1        | `AGENTS.md`                 | PM contract, CI expectations      |
| 2        | `docker-compose.yml`        | Services to validate              |
| 3        | `validate.sh`               | Validation script to run in CI    |
| 4        | `Makefile`                  | Targets to test                   |
| 5        | `docs/CHANGE_IMPACT_MAP.md` | What breaks when workflows change |

## GitHub Actions Standards

### CI Workflow (`.github/workflows/ci.yml`)

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate compose
        run: docker compose config
      - name: Run validation
        run: ./validate.sh
      - name: Shellcheck
        uses: koalaman/shellcheck-action@v1
      - name: YAML lint
        uses: ibiqlik/action-yamllint@v3
```

- Must complete in under 3 minutes
- Must run on push to main and PR to main
- Must include shellcheck, yamllint, compose validation

### Dependabot (`.github/dependabot.yml`)

```yaml
version: 2
updates:
  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

### Issue Templates

- `bug_report.md`: stack version, OS, `make up` output, expected vs actual
- `feature_request.md`: problem statement, proposed solution, DORA capability

### Branch Protection Rules

- Require PR before merging to `main`
- Require status checks to pass (CI must exist first)
- No direct pushes (admins included)

## What You MAY Do

- Create/edit `.github/workflows/*.yml`
- Create/edit `.github/dependabot.yml`
- Create/edit `.github/ISSUE_TEMPLATE/*.md`
- Create `.github/FUNDING.yml`
- Update `.github/CODEOWNERS`

## What You MUST Ask Before

- Adding external CI services (CircleCI, Jenkins pipeline for repo)
- Changing the required status check names
- Modifying branch protection rules (apply via GitHub API)

## What You MUST NEVER

- Store secrets inline in workflow files
- Use `pull_request_target` without security review
- Add self-hosted runner configuration without maintainer approval
