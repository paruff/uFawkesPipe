// model-fallback OpenCode plugin
// Implements a fallback chain across AI providers.
//
// Chain order (matches opencode.json model.fallback array):
//   1. NVIDIA NIM (via local nim-proxy)  — nvidia/qwen3-coder-480b-a35b-instruct
//   2. NVIDIA NIM alternate              — nvidia/nemotron-3-ultra-550b-a55b
//   3. Google Gemini Flash               — google/gemini-2.5-flash
//   4. Google Gemini Pro                 — google/gemini-2.5-pro
//   5. OpenCode Zen                      — opencode-zen/deepseek-v4-flash-free
//   6. OpenCode Zen alternate            — opencode-zen/mimo-v2.5-free
//
// When a model returns a rate-limit (429) or server error (5xx), the plugin
// retries with the next entry in the chain transparently.

export const ModelFallbackPlugin = async ({ config }) => {
  const chain = (config?.model?.fallback ?? []).map((m) => m.id);
  let currentIndex = 0;

  const isRetryable = (statusCode) =>
    statusCode === 429 || (statusCode >= 500 && statusCode < 600);

  return {
    // Intercept model responses and advance the chain on retryable errors.
    "model.response.error": async (error, ctx) => {
      const code = error?.statusCode ?? error?.status;

      if (!isRetryable(code)) return; // non-retryable — let it propagate

      const nextIndex = currentIndex + 1;
      if (nextIndex >= chain.length) {
        console.error(
          `[model-fallback] All ${chain.length} models exhausted. Last error: ${code}`
        );
        return;
      }

      currentIndex = nextIndex;
      const nextModel = chain[currentIndex];
      console.warn(
        `[model-fallback] ${ctx.model} returned ${code}. Switching to: ${nextModel}`
      );
      ctx.model = nextModel;
    },
  };
};
