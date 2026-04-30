import { useState } from "react";
import { Card, SkeletonNode, streamSSE } from "../api/client";

export default function SocraticThread({
  node, notebookId, card, onCardUpdate, onMarkGotIt, onMarkStuck, onReject, onCollapse,
}: {
  node: SkeletonNode;
  notebookId: string;
  card: Card | null;
  onCardUpdate: (c: Card) => void;
  onMarkGotIt: () => void;
  onMarkStuck: () => void;
  onReject: () => void;
  onCollapse: () => void;
}) {
  const [reply, setReply] = useState("");
  const [thread, setThread] = useState<{ role: string; content: string }[]>([
    { role: "assistant", content: `（关于「${node.title}」）你能先说说你目前的理解吗？` },
  ]);
  const [streaming, setStreaming] = useState("");
  const [busy, setBusy] = useState(false);

  const send = async () => {
    if (!reply.trim() || busy) return;
    const userMsg = reply;
    setReply("");
    setThread(t => [...t, { role: "user", content: userMsg }]);
    setBusy(true); setStreaming("");
    let full = "";
    await streamSSE("/api/chat/send", {
      notebook_id: notebookId,
      conversation_id: null,
      message: userMsg,
    }, d => {
      if (typeof d.content === "string") {
        full += d.content;
        setStreaming(s => s + (d.content as string));
      }
    });
    setThread(t => [...t, { role: "assistant", content: full }]);
    setStreaming("");
    setBusy(false);
  };

  // Silence unused warnings (card/onCardUpdate reserved for future use)
  void card; void onCardUpdate;

  return (
    <div style={{
      marginTop: 12, paddingTop: 14, borderTop: "1px dashed var(--border)",
    }}>
      {thread.map((m, i) => (
        <div key={i} style={{ marginBottom: 10 }}>
          <div style={{ fontSize: 10, color: "var(--text-faint)", letterSpacing: "0.09em", textTransform: "uppercase", marginBottom: 4 }}>
            {m.role === "user" ? "你" : "Noto"}
          </div>
          <div style={{ fontFamily: "var(--font-serif)", fontSize: 13, lineHeight: 1.7 }}>{m.content}</div>
        </div>
      ))}
      {streaming && (
        <div style={{ fontFamily: "var(--font-serif)", fontSize: 13, lineHeight: 1.7, color: "var(--text-muted)" }}>
          {streaming}
        </div>
      )}

      <div style={{
        background: "var(--bg-drawer)", border: "1px solid var(--border)",
        borderRadius: 6, padding: "10px 12px", marginTop: 6,
      }}>
        <textarea
          value={reply} onChange={e => setReply(e.target.value)}
          placeholder="说说你的想法..."
          style={{
            width: "100%", border: "none", background: "transparent",
            resize: "vertical", minHeight: 36, outline: "none",
            fontFamily: "var(--font-serif)", fontSize: 13, lineHeight: 1.7,
          }}
        />
      </div>

      <div style={{ marginTop: 10, display: "flex", gap: 6, flexWrap: "wrap" }}>
        <button onClick={send} disabled={busy} style={primaryBtn}>💬 提交</button>
        <button onClick={onMarkGotIt} style={btn}>✓ 懂了</button>
        <button onClick={onMarkStuck} style={btn}>⚠ 不懂</button>
        <button onClick={onReject} style={subtleBtn}>× 否决</button>
        <button onClick={onCollapse} style={subtleBtn}>收起</button>
      </div>
    </div>
  );
}

const btn: React.CSSProperties = { border: "1px solid var(--border)", background: "var(--surface)", borderRadius: 6, padding: "4px 10px", fontSize: 11, cursor: "pointer" };
const primaryBtn: React.CSSProperties = { ...btn, background: "var(--text)", color: "var(--bg)", borderColor: "var(--text)" };
const subtleBtn: React.CSSProperties = { ...btn, background: "transparent", border: "none", color: "var(--text-muted)" };
