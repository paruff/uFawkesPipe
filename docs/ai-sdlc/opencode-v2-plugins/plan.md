# Plan: Port OpenCode plugins to V2

## Intent

OpenCode 2.3.0 rejects the V1 named-export factory shape (`export const XPlugin = async (ctx) => ({ "tool.execute.before": ... })`). All four project plugins in `.opencode/plugins/` were failing to load on every boot with `Plugin must export a default definition with an id and an effect or setup function`.

This plan ports the two plugins that still serve a purpose and deletes the two that do not.

## Scope

- **graphify.js** → port to V2 default export
- **shift-left.js** → port to V2 default export (source of truth at `scripts/shift-left/opencode-plugin.js`)
- **ai-sdlc-hooks.ts** → delete (no `protected-paths.json` in this repo; git hooks + gitleaks cover secrets)
- **model-fallback.js** → delete (silent fallback contradicts determinism invariant)

## Verification Strategy

### 1. Contract Tests (node --test)

- **graphify.test.mjs**: V2 contract (`id`, `setup`), injects reminder once per session via `session.context` hook, silent when no `graphify-out/graph.json` exists
- **shift-left.test.mjs** (ported repo test `test-opencode-plugin.mjs`): shim absent, doctor failure/success, gate failure with wake, second-idle loop guard, loop-guard message, passing gate resets state, unrelated events ignored, `--no-verify` blocked in three forms

### 2. Integration via Existing Unit Suite

- `scripts/test-opencode-plugins.sh` wired into `scripts/run-unit-tests.sh` as 14th suite
- `tests/unit/test_opencode_plugins.py` pytest wrapper runs the node tests via `make test-unit`

### 3. Local Verification

```bash
# All 14 offline unit suites pass
bash scripts/run-unit-tests.sh

# Direct plugin contract test
node --test tests/plugins/graphify.test.mjs tests/plugins/shift-left.test.mjs

# OpenCode plugin list shows V2 plugins loading
opencode plugin list | grep -E "graphify|shift-left"
```

### 4. CI Gates

- Pre-commit hooks pass (including `unit-tests` which runs the 14 suites)
- Artifact chain: this plan.md with Verification Strategy in same PR
- All existing CI workflows green

## Architecture Check

- No pipeline stages, `.fawkespipe.yml` contract, `compose.yaml`, policy, or `k8s/` changes
- Only `.opencode/plugins/` and `scripts/shift-left/` modified
- No credentials added; gitleaks passes

## Acceptance Criteria

- [ ] OpenCode 2.3.0 loads all project plugins without "failed to load plugin" warnings
- [ ] 14/14 unit test suites pass (13 existing + 1 new)
- [ ] graphify reminder injects once per session when graph exists
- [ ] shift-left blocks `--no-verify` on commit/push via tool hook
- [ ] shift-left runs doctor at session.start and agent-gate on agent.idle
- [ ] Pre-commit hooks pass without `--no-verify`
