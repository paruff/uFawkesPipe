// Contract and behaviour tests for .opencode/plugins/graphify.js (OpenCode V2).
// V2 plugin definitions are `{ id, setup }`; the V1 named-export factory shape
// is rejected by the V2 supervisor before setup ever runs.
import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";

const PLUGIN = new URL("../../.opencode/plugins/graphify.js", import.meta.url);

function fakeCtx(directory) {
  const hooks = {};
  return {
    hooks,
    ctx: {
      location: { directory },
      session: {
        hook: async (name, cb) => {
          hooks[name] = cb;
          return { dispose: async () => {} };
        },
      },
      tool: { hook: async () => ({ dispose: async () => {} }) },
      event: { subscribe: () => (async function* () {})() },
    },
  };
}

async function withGraph(fn) {
  const dir = mkdtempSync(path.join(tmpdir(), "graphify-"));
  mkdirSync(path.join(dir, "graphify-out"), { recursive: true });
  writeFileSync(path.join(dir, "graphify-out", "graph.json"), "{}");
  try {
    return await fn(dir);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

test("graphify exports the V2 plugin contract", async () => {
  const mod = await import(PLUGIN);
  assert.equal(mod.default?.id, "graphify");
  assert.equal(typeof mod.default.setup, "function");
});

test("registers a context hook and injects the reminder once per session", async () => {
  await withGraph(async (dir) => {
    const { ctx, hooks } = fakeCtx(dir);
    const mod = await import(PLUGIN);
    await mod.default.setup(ctx);

    assert.equal(typeof hooks.context, "function", "no context hook registered");

    const event = {
      sessionID: "s1",
      messages: [{ role: "user", content: [{ type: "text", text: "hi" }] }],
    };
    await hooks.context(event);
    assert.match(event.messages[0].content[0].text, /\[graphify\]/);

    const count = event.messages[0].content.length;
    await hooks.context(event);
    assert.equal(event.messages[0].content.length, count, "injected twice in one session");
  });
});

test("does nothing when no graph exists", async () => {
  const dir = mkdtempSync(path.join(tmpdir(), "graphify-"));
  try {
    const { ctx, hooks } = fakeCtx(dir);
    const mod = await import(PLUGIN);
    await mod.default.setup(ctx);

    const event = {
      sessionID: "s2",
      messages: [{ role: "user", content: [{ type: "text", text: "hi" }] }],
    };
    await hooks.context(event);
    assert.equal(event.messages[0].content[0].text, "hi");
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
