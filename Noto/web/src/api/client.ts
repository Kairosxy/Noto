// ---------- Types ----------
export type SafeSettings = {
  ai_provider: string; ai_base_url: string; ai_model: string; ai_api_key_set: boolean;
  embedding_provider: string; embedding_base_url: string; embedding_model: string; embedding_api_key_set: boolean;
  supabase_url: string; supabase_service_key_set: boolean;
};

export type Notebook = { id: string; title: string; goal: string; created_at: string };

export type Document = {
  id: string; notebook_id: string; filename: string;
  mime: string | null; pages: number | null;
  status: "parsing" | "ready" | "failed";
  summary: string | null;
  created_at: string;
};

export type SkeletonNode = {
  id: string; node_type: "claim" | "concept" | "question" | "pitfall";
  title: string; body: string | null;
  source_positions: { document_id: string; chunk_id?: string; page_num?: number }[] | null;
  card_source: string;
  rejected_at: string | null;
  merged_into: string | null;
};

export type LearningDirection = {
  id: string; position: number; title: string; description: string | null;
  estimated_minutes: number | null; node_ids: string[];
};

export type Skeleton = {
  id: string | null;
  notebook_id?: string;
  space_summary: string | null;
  status: "not_generated" | "generating" | "ready" | "failed";
  directions: LearningDirection[];
  nodes: SkeletonNode[];
};

export type Card = {
  id: string; notebook_id: string;
  skeleton_node_id: string | null;
  question: string; answer: string;
  user_explanation: string | null;
  card_state: "unread" | "thinking" | "got_it" | "stuck";
  due_at: string; ease: number; reps: number;
};

export type EvalResult = {
  verdict: "pass" | "can_deepen";
  feedback: string;
  missing_points: string[];
};

export type Highlight = {
  id: string; document_id: string; notebook_id: string;
  chunk_id: string | null; text: string; created_at: string;
};

// ---------- Fetch helpers ----------
async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const resp = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init.headers || {}) },
  });
  if (!resp.ok) {
    const detail = await resp.text();
    throw new Error(`${resp.status}: ${detail}`);
  }
  if (resp.headers.get("content-type")?.includes("application/json")) {
    return resp.json();
  }
  return {} as T;
}

// ---------- API surfaces ----------
export const api = {
  getSettings: () => req<SafeSettings>("/api/settings"),
  updateSettings: (body: Record<string, string>) =>
    req<SafeSettings>("/api/settings", { method: "POST", body: JSON.stringify(body) }),
  testConnection: (body: { provider: string; api_key: string; base_url?: string; model?: string }) =>
    req<{ success: boolean; message: string }>("/api/ai/test-connection", {
      method: "POST", body: JSON.stringify(body),
    }),
};

export const notebooksApi = {
  list: () => req<Notebook[]>("/api/notebooks"),
  get: (id: string) => req<Notebook>(`/api/notebooks/${id}`),
  create: (body: { title: string; goal: string }) =>
    req<Notebook>("/api/notebooks", { method: "POST", body: JSON.stringify(body) }),
  patch: (id: string, body: { title?: string; goal?: string }) =>
    req<Notebook>(`/api/notebooks/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  listDocuments: (id: string) => req<Document[]>(`/api/notebooks/${id}/documents`),
};

export const skeletonApi = {
  get: (notebookId: string) => req<Skeleton>(`/api/notebooks/${notebookId}/skeleton`),
  regenerate: (notebookId: string) =>
    req<{ skeleton_id: string; status: string }>(
      `/api/notebooks/${notebookId}/skeleton/regenerate`,
      { method: "POST" },
    ),
  rejectNode: (nodeId: string, reason: string) =>
    req(`/api/skeleton-nodes/${nodeId}/reject`, { method: "POST", body: JSON.stringify({ reason }) }),
  mergeNode: (nodeId: string, target_node_id: string) =>
    req(`/api/skeleton-nodes/${nodeId}/merge-into`, { method: "POST", body: JSON.stringify({ target_node_id }) }),
  backfillSummaries: (notebookId: string) =>
    req<{ count: number; status: string }>(
      `/api/notebooks/${notebookId}/documents/backfill-summaries`,
      { method: "POST" },
    ),
};

export const docsApi = {
  get: (id: string) => req<Document>(`/api/ingest/document/${id}`),
  getSummary: (id: string) => req<{ document_id: string; summary: string | null }>(`/api/ingest/document/${id}/summary`),
  regenerateSummary: (id: string) =>
    req<{ document_id: string; summary: string }>(`/api/ingest/document/${id}/summary/regenerate`, { method: "POST" }),
  getChunks: (id: string) => req<{ id: string; content: string; page_num: number | null; position: number }[]>(`/api/ingest/document/${id}/chunks`),
};

export const cardsApi = {
  list: (notebookId: string, state?: string) =>
    req<Card[]>(`/api/cards?notebook_id=${notebookId}${state ? `&state=${state}` : ""}`),
  ensureForNode: (nodeId: string) =>
    req<Card>(`/api/cards/ensure-for-node/${nodeId}`, { method: "POST" }),
  updateState: (cardId: string, body: { state: Card["card_state"]; user_explanation?: string }) =>
    req<Card>(`/api/cards/${cardId}/state`, { method: "PATCH", body: JSON.stringify(body) }),
  evaluate: (cardId: string, user_explanation: string) =>
    req<EvalResult>(`/api/cards/${cardId}/evaluate`, {
      method: "POST",
      body: JSON.stringify({ card_id: cardId, user_explanation }),
    }),
};

export const reviewApi = {
  due: (notebookId: string) => req<Card[]>(`/api/review/due?notebook_id=${notebookId}`),
  rate: (body: { card_id: string; rating: "again" | "hard" | "good" | "easy" }) =>
    req<{ due_at: string; ease: number; reps: number }>("/api/review/rate", {
      method: "POST", body: JSON.stringify(body),
    }),
};

export const highlightsApi = {
  list: (documentId: string) => req<Highlight[]>(`/api/highlights?document_id=${documentId}`),
  create: (body: { document_id: string; chunk_id?: string; text: string }) =>
    req<Highlight>("/api/highlights", { method: "POST", body: JSON.stringify(body) }),
  delete: (id: string) => req(`/api/highlights/${id}`, { method: "DELETE" }),
};

// ---------- SSE ----------
export async function streamSSE(
  path: string,
  body: unknown,
  onChunk: (data: Record<string, unknown>) => void,
): Promise<string> {
  const resp = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok || !resp.body) throw new Error(`SSE failed: ${resp.status}`);
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buf = ""; let full = "";
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
      } catch { /* skip */ }
    }
  }
  return full;
}

export async function uploadDocument(notebookId: string, file: File) {
  const fd = new FormData();
  fd.append("notebook_id", notebookId);
  fd.append("file", file);
  const resp = await fetch("/api/ingest/upload", { method: "POST", body: fd });
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json() as Promise<{ document_id: string; status: string }>;
}

export async function askWithContext(body: {
  notebook_id: string; document_id: string; chunk_id?: string;
  selected_text: string; user_question: string;
  action: "ask" | "mark_stuck" | "save_note";
}) {
  return req<{ reply: string | null; node_id: string | null; card_id: string | null }>(
    "/api/chat/ask-with-context",
    { method: "POST", body: JSON.stringify(body) },
  );
}
