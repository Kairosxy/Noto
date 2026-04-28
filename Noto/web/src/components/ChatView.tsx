import { FormEvent, useEffect, useRef, useState } from "react";
import { chatApi, chatApiExt, Message, streamSSE } from "../api/client";
import CitationPanel from "./CitationPanel";

export default function ChatView({ notebookId }: { notebookId: string }) {
  const [convId, setConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [streaming, setStreaming] = useState("");
  const [input, setInput] = useState("");
  const [citations, setCitations] = useState<{ chunk_id: string; page_num: number | null }[]>([]);
  const [busy, setBusy] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!convId) return;
    chatApi.listMessages(convId).then(setMessages);
  }, [convId]);

  useEffect(() => () => abortRef.current?.abort(), []);

  const onSend = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || busy) return;
    const userMsg = input;
    setInput("");
    setBusy(true);
    setStreaming("");

    setMessages((m) => [...m, {
      id: "tmp-" + Date.now(),
      conversation_id: convId ?? "",
      role: "user",
      content: userMsg,
      citations: null,
      created_at: new Date().toISOString(),
    }]);

    const ctrl = new AbortController();
    abortRef.current = ctrl;
    let effectiveConvId = convId;
    try {
      await streamSSE(
        "/api/chat/send",
        { notebook_id: notebookId, conversation_id: convId, message: userMsg },
        (d) => {
          if (d.conversation_id && !effectiveConvId) {
            effectiveConvId = d.conversation_id;
            setConvId(d.conversation_id);
          }
          if (d.citations) setCitations(d.citations);
          if (d.content) setStreaming((s) => s + d.content);
          if (d.error) setStreaming((s) => s + `\n[ERROR] ${d.error}`);
        },
        ctrl.signal,
      );
      if (effectiveConvId) setMessages(await chatApi.listMessages(effectiveConvId));
    } catch (err) {
      if ((err as { name?: string }).name !== "AbortError") throw err;
    } finally {
      abortRef.current = null;
      setStreaming("");
      setBusy(false);
    }
  };

  const onClose = async () => {
    if (!convId) return;
    if (!confirm("结束本轮并提炼复习卡？")) return;
    const r = await chatApiExt.close(convId);
    alert(`已生成 ${r.cards.length} 张复习卡`);
    setConvId(null);
    setMessages([]);
    setCitations([]);
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 12 }}>
      <div>
        <div className="card" style={{ minHeight: 300 }}>
          {messages.length === 0 && !streaming && <p style={{ color: "#888" }}>发一条消息开始学习。</p>}
          {messages.map((m) => (
            <div key={m.id} style={{ marginBottom: 12 }}>
              <strong>{m.role === "user" ? "你" : "Noto"}：</strong>
              <div style={{ whiteSpace: "pre-wrap" }}>{m.content}</div>
            </div>
          ))}
          {streaming && (
            <div style={{ marginBottom: 12 }}>
              <strong>Noto：</strong>
              <div style={{ whiteSpace: "pre-wrap" }}>{streaming}</div>
            </div>
          )}
        </div>
        <form onSubmit={onSend}>
          <input value={input} disabled={busy} onChange={(e) => setInput(e.target.value)} placeholder="说说你的理解..." />
          <button className="primary" type="submit" disabled={busy} style={{ marginTop: 8 }}>
            {busy ? "回答中..." : "发送"}
          </button>
          <button type="button" onClick={onClose} disabled={!convId || busy} style={{ marginLeft: 8 }}>
            结束本轮
          </button>
        </form>
      </div>
      <CitationPanel citations={citations} />
    </div>
  );
}
