export type SafeSettings = {
  ai_provider: string;
  ai_base_url: string;
  ai_model: string;
  ai_api_key_set: boolean;
  embedding_provider: string;
  embedding_base_url: string;
  embedding_model: string;
  embedding_api_key_set: boolean;
  supabase_url: string;
  supabase_service_key_set: boolean;
};

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const resp = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init.headers || {}) },
  });
  if (!resp.ok) {
    const detail = await resp.text();
    throw new Error(`${resp.status}: ${detail}`);
  }
  return resp.json();
}

export const api = {
  getSettings: () => req<SafeSettings>("/api/settings"),
  updateSettings: (body: Record<string, string>) =>
    req<SafeSettings>("/api/settings", { method: "POST", body: JSON.stringify(body) }),
  testConnection: (body: { provider: string; api_key: string; base_url?: string; model?: string }) =>
    req<{ success: boolean; message: string }>("/api/ai/test-connection", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};

/** 消费 SSE 流；onChunk 收到 {content|error} 逐片；resolved 时返回完整文本 */
export async function streamSSE(
  path: string,
  body: unknown,
  onChunk: (data: { content?: string; error?: string }) => void,
): Promise<string> {
  const resp = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok || !resp.body) throw new Error(`SSE failed: ${resp.status}`);
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  let full = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const parts = buf.split("\n\n");
    buf = parts.pop() ?? "";
    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data:")) continue;
      const payload = line.slice(5).trim();
      if (payload === "[DONE]") return full;
      try {
        const obj = JSON.parse(payload);
        if (typeof obj.content === "string") full += obj.content;
        onChunk(obj);
      } catch {
        // skip
      }
    }
  }
  return full;
}
