// graphify OpenCode plugin (V2)
// Injects a knowledge-graph reminder into the session when the graph exists.
//
// OpenCode V2 loads a plugin through its default export — `{ id, setup }`.
// The V1 named-export factory (`export const XPlugin = async (ctx) => ({...})`)
// is rejected before setup runs. V2 also has no `tool.execute.before` hook with
// a mutable output, so the reminder is delivered as context on the session's
// `context` hook instead of being prepended to a bash command.
import { existsSync } from "node:fs";
import path from "node:path";

const REMINDER =
  '[graphify] Knowledge graph at graphify-out/. For focused questions, run `graphify query "<question>"` (scoped subgraph, usually much smaller than GRAPH_REPORT.md) instead of grepping raw files. Read GRAPH_REPORT.md only for broad architecture context.';

export default {
  id: "graphify",
  async setup(ctx) {
    const directory = ctx.location?.directory;
    if (!directory) return;

    const graph = path.join(directory, "graphify-out", "graph.json");
    const reminded = new Set();

    await ctx.session.hook("context", (event) => {
      // The graph can appear after the session starts, so check on every turn.
      if (!existsSync(graph)) return;

      const sessionID = event?.sessionID;
      if (sessionID && reminded.has(sessionID)) return;

      const messages = event?.messages;
      if (!Array.isArray(messages) || messages.length === 0) return;

      const user = messages.find((m) => m?.role === "user");
      if (!user) return;
      if (!Array.isArray(user.content)) user.content = [];

      // Never duplicate the reminder if it is already in the request.
      if (user.content.some((p) => p?.type === "text" && typeof p.text === "string" && p.text.includes("[graphify]"))) {
        if (sessionID) reminded.add(sessionID);
        return;
      }

      user.content.unshift({ type: "text", text: REMINDER });
      if (sessionID) reminded.add(sessionID);
    });
  },
};
