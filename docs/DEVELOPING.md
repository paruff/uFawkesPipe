# Developing the pipeline

Three commands, all run in Docker (no host installs). Run them before you push a
change to `.woodpecker.yml`.

```bash
make lint-ci     # woodpecker-cli lint: schema and structure, no server needed
make precommit   # every hook, incl. woodpecker-lint and POSIX-sh shellcheck
make ci-exec     # run the pipeline locally with --pipeline-event push
```

- Steps run under `/bin/sh`, not bash: no `source`, `[[ ]]`, arrays or `${var:0:7}`.
- `make ci-exec` reads secrets from the gitignored `.ci-exec-secrets.yaml`; never use
  real ones. `CI_FILE=path` runs a different pipeline.
- Rules and approvals: `AGENTS.md` sections 4 and 5.
