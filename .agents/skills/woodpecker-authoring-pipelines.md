---
name: woodpecker-authoring-pipelines
description: Validate Woodpecker config before pushing and debug "works locally, fails in CI" with a probe step. Load when editing .woodpecker.yml, giving a step a secret, or when a step behaves differently than it does locally.
applies: .woodpecker.yml
---

# Authoring Woodpecker pipelines

> Third-party, MIT: adapted from `woodpecker-authoring-pipelines` in
> technicalpickles/pickled-claude-plugins (plugins/woodpecker), reviewed and trimmed
> for this repo. Repo rules live in `woodpecker-pipeline-conventions`; those win on conflict.

## Validate before pushing

```bash
make lint-ci    # woodpecker-cli lint in Docker; no server, no login
```

A warning like "add a `when` block with an `event` filter" is advice for the CLI, but
in this repo it is treated as a defect: without a filter a step runs on every event.

`woodpecker-cli exec` runs a pipeline locally. It defaults the event to `manual`, which
skips every step filtered to `push`, so always pass `--pipeline-event push`
(`make ci-exec` does).

## "Works locally, fails in CI"

The shell, the user a step runs as, service names and the checkout all depend on the
backend, image and settings. Do not assume them. Add a throwaway probe step, read its
log, fix against what it shows, then delete the probe:

```yaml
  - name: probe
    image: <the same image the failing step uses>
    commands:
      - id                      # user the step runs as
      - ls -l /bin/sh           # which shell commands run under
      - echo "$CI_PIPELINE_EVENT $CI_COMMIT_BRANCH"
      - ls -ld .git             # directory or file
```

## Documented behaviour

- `failure: ignore` lets a step fail without failing the pipeline: a green pipeline can
  contain a red step. Remove it when the check should gate merges.
- Steps after a failure are skipped unless they opt in with `when: status: [failure]`.

## Secrets

A step reads a secret with `from_secret` under `environment:` (or `settings:` for a plugin).

- **Events:** a secret is not exposed to `pull_request` pipelines unless that event is
  enabled on the secret.
- **Image filter:** leave it empty for a step with `commands:`. A filtered secret used by a
  normal step fails the whole pipeline before any step runs ("is only allowed to be used by
  plugins").

## Local `exec` flags

`--backend-engine docker`, `--local`, `--repo-path`, `--commit-branch` (default `main`).
In a linked git worktree `.git` is a file; point `--repo-path` at a regular clone if a
step calls git.
