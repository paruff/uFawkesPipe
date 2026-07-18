# PR Standards — uFawkesPipe

## Title Format

PR titles follow **Conventional Commits**:

```
type(scope): description
```

| Type     | When to Use                                                |
| -------- | ---------------------------------------------------------- |
| `feat`   | New pipeline stage, contract field, or workflow            |
| `fix`    | Bug fix, configuration correction                          |
| `docs`   | Documentation-only changes                                 |
| `chore`  | Maintenance, dependency updates, tooling                   |
| `refactor` | Code/configuration restructuring with no behavior change |
| `test`   | Adding or fixing tests                                     |
| `ci`     | CI/CD pipeline or workflow changes                         |

**Rules:**
- Scope is recommended: `feat(pipeline):`, `fix(preflight):`
- First word after `:` must be **lowercase**
- No trailing period
- Max 72 characters for the title line

## Branch Naming

```
feat/<short-slug>
fix/<short-slug>
chore/<short-slug>
docs/<short-slug>
```

## PR Body

Every PR must include the AI-Assisted Review Block (see `AGENTS.md §7`), plus:

- **Pipeline stages affected**
- **How tested** — local `make validate` + workflow run
- **Breaking change check** — did `.fawkespipe.yml` contract change? If so, migration guide written?
- **Credentials check** — nothing sensitive committed

## CI Requirements

Before a PR can merge:

- [ ] All CI checks pass (pre-commit, lint, security, build, tests)
- [ ] `main-ci-guard` passes (CI on main is green)
- [ ] PR size is under 400 lines (or has `large-pr-approved` label)
- [ ] Review has been approved
- [ ] Verification has passed

## Pipeline Contract Changes

PRs that modify `.fawkespipe.yml` fields must include:
- Migration example in `examples/`
- Documentation update in `docs/pipeline-contract.md`
- Note in PR body about backward compatibility
