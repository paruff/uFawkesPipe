---
name: woodpecker-pipeline-conventions
description: Rules for editing uFawkesPipe's own Woodpecker pipeline - image pinning, secrets, approvals, POSIX sh. Load before changing .woodpecker.yml. Rules come from AGENTS.md sections 4 and 5; this is a checklist, not a tutorial.
applies: .woodpecker.yml
---

# Woodpecker Pipeline Conventions

> Load before editing `.woodpecker.yml`. Source of truth: `AGENTS.md` sections 4 and 5.

## Always

- **Pin every image** to an exact tag. Never `latest`, never an untagged image.
- **Secrets** come from Woodpecker's secret store (`from_secret`) or the gitignored .env file. Never inline
  in the pipeline YAML, never committed.
- **Steps run under `/bin/sh`**, not bash. No `source` (use `.`), `[[ ]]`, arrays,
  `${var:0:7}` or `$PIPESTATUS`. A step that needs bash installs it explicitly.
- **Stage order**: Checkout, Build, Test, Security Scan, Publish, Deploy.
- **Every step logs** start and finish through `scripts/dora-log.sh`.
- Give each step a `when:` event filter. Treat the linter's "add an event filter"
  warning as a defect.
- `depends_on` uses the step name exactly as declared in this file.
- Declare CI jobs in the file. Never create them in the Woodpecker UI.

## Ask the owner first

- Changing a Woodpecker image or plugin version.
- Adding a stage or step to the standard pipeline.
- Anything that touches the .fawkespipe.yml contract fields or `compose.yaml` structure.

## Before you push

Run `make lint-ci`, then `make precommit`. Both run in Docker with no host installs.
Check `docs/CHANGE_IMPACT_MAP.md` when a change crosses planes.
