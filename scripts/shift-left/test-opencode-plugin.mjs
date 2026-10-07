// scripts/shift-left/test-opencode-plugin.mjs — the OpenCode plugin runs the
// shift-left doctor at session start and the agent gate when the agent goes
// idle, and refuses the hook-skipping git flag. A fake OpenCode client and a
// stub shim stand in for both. Run through test-opencode-plugin.sh (node:test,
// no dependencies).
import assert from "node:assert/strict";
import { chmodSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { pathToFileURL } from "node:url";

const here = path.dirname(new URL(import.meta.url).pathname);
const { ShiftLeft } = await import(pathToFileURL(path.join(here, "opencode-plugin.js")).href);

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

function fakeClient() {
  const prompts = [];
  return {
    prompts,
    client: { session: { prompt: async (req) => void prompts.push(req) } },
  };
}

async function plugin(r) {
  const c = fakeClient();
  const hooks = await ShiftLeft({ client: c.client, directory: r.dir });
  return { hooks, prompts: c.prompts };
}
const created = (id = "s1") => ({ event: { type: "session.created", properties: { info: { id } } } });
const idle = (id = "s1") => ({ event: { type: "session.idle", properties: { sessionID: id } } });

test("without a shim the plugin does nothing", async () => {
  const r = repo({ shim: false });
  const { hooks, prompts } = await plugin(r);
  await hooks.event(created());
  await hooks.event(idle());
  assert.equal(prompts.length, 0);
});

test("session start: a doctor problem goes into the session without a reply", async () => {
  const r = repo();
  r.set("doctor", { rc: 1, out: "  FAIL  D1  pre-push is not installed\n        fix: pre-commit install\n" });
  const { hooks, prompts } = await plugin(r);
  await hooks.event(created());
  assert.match(r.calls(), /^doctor --quiet/m);
  assert.equal(prompts.length, 1);
  assert.equal(prompts[0].path.id, "s1");
  assert.equal(prompts[0].body.noReply, true);
  assert.match(prompts[0].body.parts[0].text, /pre-commit install/);
});

test("session start: a healthy doctor is silent", async () => {
  const r = repo();
  const { hooks, prompts } = await plugin(r);
  await hooks.event(created());
  assert.equal(prompts.length, 0);
});

test("idle: a failing gate sends the failure back to the agent, which then replies", async () => {
  const r = repo();
  r.set("agent-gate", { rc: 2, err: "agent gate: commit-stage hooks fail on your uncommitted changes\nruff failed\n" });
  const { hooks, prompts } = await plugin(r);
  await hooks.event(idle());
  assert.match(r.calls(), /^agent-gate/m);
  assert.match(r.calls(), /"stop_hook_active": ?false/);
  assert.equal(prompts.length, 1);
  assert.notEqual(prompts[0].body.noReply, true, "the agent must answer, so it keeps working");
  assert.match(prompts[0].body.parts[0].text, /ruff failed/);
});

test("idle: a second idle after the same prompt tells the gate it already blocked once", async () => {
  const r = repo();
  r.set("agent-gate", { rc: 2, err: "still failing\n" });
  const { hooks } = await plugin(r);
  await hooks.event(idle());
  await hooks.event(idle());
  assert.match(r.calls(), /"stop_hook_active": ?true/);
});

test("idle: the loop guard's message is shown, not turned into another round", async () => {
  const r = repo();
  r.set("agent-gate", { rc: 0, out: '{"systemMessage": "stopped instead of looping"}\n' });
  const { hooks, prompts } = await plugin(r);
  await hooks.event(idle());
  assert.equal(prompts.length, 1);
  assert.equal(prompts[0].body.noReply, true);
  assert.match(prompts[0].body.parts[0].text, /stopped instead of looping/);
});

test("idle: a passing gate is silent and resets the retry state", async () => {
  const r = repo();
  r.set("agent-gate", { rc: 2, err: "bad\n" });
  const { hooks, prompts } = await plugin(r);
  await hooks.event(idle());
  r.set("agent-gate", { rc: 0 });
  await hooks.event(idle());
  assert.equal(prompts.length, 1, "no new prompt once it passes");
  r.set("agent-gate", { rc: 2, err: "bad again\n" });
  await hooks.event(idle());
  const log = r.calls().split("\n").filter((l) => l.includes("stop_hook_active"));
  assert.match(log[log.length - 1], /false/, "a new failure starts a fresh round");
});

test("other events are ignored", async () => {
  const r = repo();
  r.set("agent-gate", { rc: 2, err: "bad\n" });
  const { hooks, prompts } = await plugin(r);
  await hooks.event({ event: { type: "session.updated", properties: {} } });
  assert.equal(prompts.length, 0);
  assert.equal(r.calls(), "");
});

test("tool.execute.before refuses skipping hooks on a real commit or push", async () => {
  const r = repo();
  const { hooks } = await plugin(r);
  const run = (command) => hooks["tool.execute.before"]({ tool: "bash", sessionID: "s1", callID: "c" }, { args: { command } });
  await assert.rejects(run(`git commit ${SKIP_HOOKS} -m x`), /hooks/i);
  await assert.rejects(run(`git push ${SKIP_HOOKS} origin main`), /hooks/i);
  await assert.rejects(run(`cd x && git -C y commit -m z ${SKIP_HOOKS}`), /hooks/i);
  await run("git commit -m x");
  await run(`echo "never use git commit ${SKIP_HOOKS}"`);
  await hooks["tool.execute.before"]({ tool: "edit", sessionID: "s1", callID: "c" }, { args: { filePath: "a" } });
});
