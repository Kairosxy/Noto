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

export type Notebook = { id: string; title: string; goal: string; created_at: string };
export type Document = {
  id: string; notebook_id: string; filename: string;
  mime: string | null; pages: number | null;
  status: "parsing" | "ready" | "failed"; created_at: string;
};
export type Message = {
  id: string; conversation_id: string;
  role: "user" | "assistant"; content: string;
  citations: { chunk_id: string; page_num: number | null }[] | null;
  created_at: string;
};
export type Conversation = {
  id: string; notebook_id: string; title: string;
  status: "active" | "closed"; started_at: string; closed_at: string | null;
};

export const notebooksApi = {
  list: () => req<Notebook[]>("/api/notebooks"),
  create: (body: { title: string; goal: string }) =>
    req<Notebook>("/api/notebooks", { method: "POST", body: JSON.stringify(body) }),
  get: (id: string) => req<Notebook>(`/api/notebooks/${id}`),
  listDocuments: (id: string) => req<Document[]>(`/api/notebooks/${id}/documents`),
};

export const chatApi = {
  listConversations: (notebookId: string) =>
    req<Conversation[]>(`/api/chat/conversations?notebook_id=${notebookId}`),
  listMessages: (convId: string) => req<Message[]>(`/api/chat/messages?conversation_id=${convId}`),
};

export async function uploadDocument(notebookId: string, file: File): Promise<{ document_id: string; status: string }> {
  const fd = new FormData();
  fd.append("notebook_id", notebookId);
  fd.append("file", file);
  const resp = await fetch("/api/ingest/upload", { method: "POST", body: fd });
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}

export type Card = {
  id: string; notebook_id: string;
  question: string; answer: string;
  due_at: string; ease: number; reps: number;
};

export const reviewApi = {
  due: (notebookId: string) => req<Card[]>(`/api/review/due?notebook_id=${notebookId}`),
  rate: (body: { card_id: string; rating: "again" | "hard" | "good" | "easy" }) =>
    req<{ due_at: string; ease: number; reps: number }>("/api/review/rate", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};

export const chatApiExt = {
  close: (conversation_id: string) =>
    req<{ ok: boolean; cards: { question: string; answer: string }[] }>(
      "/api/chat/close-conversation",
      { method: "POST", body: JSON.stringify({ conversation_id }) },
    ),
};
