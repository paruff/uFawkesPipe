// scripts/shift-left/test-opencode-plugin.mjs — the OpenCode V2 plugin runs the
// shift-left doctor at session start and the agent gate when the agent goes
// idle, and refuses the hook-skipping git flag. A fake plugin Context and a
// stub shim stand in for both. Run through test-opencode-plugin.sh (node:test,
// no dependencies).
import assert from "node:assert/strict";
import { chmodSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { pathToFileURL } from "node:url";

const here = path.dirname(new URL(import.meta.url).pathname);
const { default: shiftLeft } = await import(
  pathToFileURL(path.join(here, "opencode-plugin.js")).href
);

// The flag the plugin must refuse, built here so the test source never spells
// it next to "git commit" (a hook that scans commands would trip on the text).
const SKIP_HOOKS = ["--no", "verify"].join("-");

// A repo whose scripts/shift-left.sh is a stub: each tool's exit code and
// output come from files, and its arguments and stdin are logged.
function repo({ shim = true } = {}) {
  const dir = mkdtempSync(path.join(tmpdir(), "oc-plugin-"));
  mkdirSync(path.join(dir, "scripts"), { recursive: true });
  if (shim) {
    writeFileSync(
      path.join(dir, "scripts/shift-left.sh"),
      `#!/usr/bin/env bash
root="$(cd "$(dirname "$0")/.." && pwd)"
tool="$1"; shift
{ echo "$tool $*"; cat; echo; } >> "$root/calls.log"
[[ -f "$root/$tool.out" ]] && cat "$root/$tool.out"
[[ -f "$root/$tool.err" ]] && cat "$root/$tool.err" >&2
exit "$(cat "$root/$tool.rc" 2>/dev/null || echo 0)"
`,
    );
    chmodSync(path.join(dir, "scripts/shift-left.sh"), 0o755);
  }
  return {
    dir,
    set(tool, { rc = 0, out = "", err = "" }) {
      writeFileSync(path.join(dir, `${tool}.rc`), String(rc));
      writeFileSync(path.join(dir, `${tool}.out`), out);
      writeFileSync(path.join(dir, `${tool}.err`), err);
    },
    calls() {
      try {
        return readFileSync(path.join(dir, "calls.log"), "utf8");
      } catch {
        return "";
      }
    },
  };
}

// The V2 plugin Context surface this plugin uses: typed tool hooks, a session
// stream, and prompt/synthetic notices. `push` feeds the session stream.
function fakeContext(directory) {
  const prompts = [];
  const toolHooks = {};
  const queue = [];
  let wake = null;
  const push = (event) => {
    queue.push(event);
    if (wake) {
      const w = wake;
      wake = null;
      w();
    }
  };
  const ctx = {
    location: { directory },
    tool: {
      hook: async (name, cb) => {
        toolHooks[name] = cb;
        return { dispose: async () => {} };
      },
    },
    session: {
      prompt: async (input) => void prompts.push({ kind: "prompt", ...input }),
      synthetic: async (input) => void prompts.push({ kind: "synthetic", ...input }),
    },
    event: {
      subscribe: ({ signal } = {}) =>
        (async function* () {
          while (!signal?.aborted) {
            if (queue.length === 0) {
              await new Promise((resolve) => {
                wake = resolve;
              });
              continue;
            }
            yield queue.shift();
          }
        })(),
    },
  };
  return { ctx, toolHooks, prompts, push };
}

async function plugin(r) {
  const fake = fakeContext(r.dir);
  const dispose = await shiftLeft.setup(fake.ctx);
  return { ...fake, dispose };
}

async function until(predicate, label, ms = 2000) {
  const start = Date.now();
  while (!predicate()) {
    if (Date.now() - start > ms) throw new Error(`timed out waiting for ${label}`);
    await new Promise((resolve) => setTimeout(resolve, 5));
  }
}

const settle = () => new Promise((resolve) => setTimeout(resolve, 30));
const created = (id = "s1") => ({ type: "session.created", data: { sessionID: id } });
const idle = (id = "s1") => ({ type: "session.idle", data: { sessionID: id } });

test("without a shim the plugin does nothing", async () => {
  const r = repo({ shim: false });
  const { push, prompts, toolHooks } = await plugin(r);
  push(created());
  push(idle());
  await settle();
  assert.equal(prompts.length, 0);
  assert.equal(toolHooks["execute.before"], undefined);
});

test("session start: a doctor problem goes into the session without a reply", async () => {
  const r = repo();
  r.set("doctor", { rc: 1, out: "  FAIL  D1  pre-push is not installed\n        fix: pre-commit install\n" });
  const { push, prompts } = await plugin(r);
  push(created());
  await until(() => prompts.length === 1, "doctor notice");
  assert.match(r.calls(), /^doctor --quiet/m);
  assert.equal(prompts[0].kind, "synthetic", "a doctor note must not wake the agent");
  assert.equal(prompts[0].resume, false);
  assert.equal(prompts[0].sessionID, "s1");
  assert.match(prompts[0].text, /pre-commit install/);
});

test("session start: a healthy doctor is silent", async () => {
  const r = repo();
  const { push, prompts } = await plugin(r);
  push(created());
  await until(() => r.calls().includes("doctor"), "doctor run");
  await settle();
  assert.equal(prompts.length, 0);
});

test("idle: a failing gate sends the failure back to the agent, which then replies", async () => {
  const r = repo();
  r.set("agent-gate", { rc: 2, err: "agent gate: commit-stage hooks fail on your uncommitted changes\nruff failed\n" });
  const { push, prompts } = await plugin(r);
  push(idle());
  await until(() => prompts.length === 1, "gate prompt");
  assert.match(r.calls(), /^agent-gate/m);
  assert.match(r.calls(), /"stop_hook_active": ?false/);
  assert.equal(prompts[0].kind, "prompt", "the agent must answer, so it keeps working");
  assert.match(prompts[0].text, /ruff failed/);
});

test("idle: a second idle after the same prompt tells the gate it already blocked once", async () => {
  const r = repo();
  r.set("agent-gate", { rc: 2, err: "still failing\n" });
  const { push, prompts } = await plugin(r);
  push(idle());
  await until(() => prompts.length === 1, "first gate prompt");
  push(idle());
  await until(() => /"stop_hook_active": ?true/.test(r.calls()), "stop_hook_active true");
});

test("idle: the loop guard's message is shown, not turned into another round", async () => {
  const r = repo();
  r.set("agent-gate", { rc: 0, out: '{"systemMessage": "stopped instead of looping"}\n' });
  const { push, prompts } = await plugin(r);
  push(idle());
  await until(() => prompts.length === 1, "loop-guard notice");
  assert.equal(prompts[0].kind, "synthetic");
  assert.match(prompts[0].text, /stopped instead of looping/);
});

test("idle: a passing gate is silent and resets the retry state", async () => {
  const r = repo();
  r.set("agent-gate", { rc: 2, err: "bad\n" });
  const { push, prompts } = await plugin(r);
  push(idle());
  await until(() => prompts.length === 1, "first failure");
  r.set("agent-gate", { rc: 0 });
  push(idle());
  await settle();
  assert.equal(prompts.length, 1, "no new prompt once it passes");
  r.set("agent-gate", { rc: 2, err: "bad again\n" });
  push(idle());
  await until(() => prompts.length === 2, "second failure");
  const log = r.calls().split("\n").filter((l) => l.includes("stop_hook_active"));
  assert.match(log[log.length - 1], /false/, "a new failure starts a fresh round");
});

test("other events are ignored", async () => {
  const r = repo();
  r.set("agent-gate", { rc: 2, err: "bad\n" });
  const { push, prompts } = await plugin(r);
  push({ type: "session.updated", data: {} });
  await settle();
  assert.equal(prompts.length, 0);
  assert.equal(r.calls(), "");
});

test("execute.before refuses skipping hooks on a real commit or push", async () => {
  const r = repo();
  const { toolHooks } = await plugin(r);
  const run = (command) => toolHooks["execute.before"]({ tool: "bash", input: { command } });
  assert.throws(() => run(`git commit ${SKIP_HOOKS} -m x`), /hooks/i);
  assert.throws(() => run(`git push ${SKIP_HOOKS} origin main`), /hooks/i);
  assert.throws(() => run(`cd x && git -C y commit -m z ${SKIP_HOOKS}`), /hooks/i);
  assert.doesNotThrow(() => run("git commit -m x"));
  assert.doesNotThrow(() => run(`echo "never use git commit ${SKIP_HOOKS}"`));
  assert.doesNotThrow(() =>
    toolHooks["execute.before"]({ tool: "edit", input: { filePath: "a" } }),
  );
});
