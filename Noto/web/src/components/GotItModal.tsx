import { useState } from "react";
import { Card, EvalResult, SkeletonNode, cardsApi } from "../api/client";

export default function GotItModal({
  node, card, onClose, onSuccess,
}: {
  node: SkeletonNode;
  card: Card;
  onClose: () => void;
  onSuccess: (updated: Card) => void;
}) {
  const [text, setText] = useState("");
  const [result, setResult] = useState<EvalResult | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (!text.trim() || busy) return;
    setBusy(true);
    const r = await cardsApi.evaluate(card.id, text);
    setResult(r);
    setBusy(false);
  };

  const confirm = async () => {
    const updated = await cardsApi.updateState(card.id, { state: "got_it", user_explanation: text });
    onSuccess(updated);
  };

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(42,37,32,0.35)",
      display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100,
    }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{
        background: "var(--surface)", borderRadius: 14, padding: 24,
        maxWidth: 520, width: "90%", boxShadow: "0 12px 32px rgba(42,37,32,0.15)",
      }}>
        <h2 style={{ fontFamily: "var(--font-serif)", fontSize: 18, fontWeight: 600, marginBottom: 6 }}>
          {result ? "AI 反馈" : "请用你自己的话解释"}
        </h2>
        <div style={{ color: "var(--text-muted)", fontSize: 12, marginBottom: 16 }}>
          「{node.title}」
        </div>

        {!result ? (
          <>
            <textarea value={text} onChange={e => setText(e.target.value)}
              placeholder="不追求完美，用自己的话说清楚就行。"
              style={{
                width: "100%", minHeight: 120, padding: "12px 14px",
                border: "1px solid var(--border)", borderRadius: 6,
                fontFamily: "var(--font-serif)", fontSize: 14, lineHeight: 1.7, outline: "none",
              }} />
            <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 14 }}>
              <button onClick={onClose} style={btn}>取消</button>
              <button onClick={submit} disabled={busy} style={primaryBtn}>
                {busy ? "评判中..." : "📊 提交评判"}
              </button>
            </div>
          </>
        ) : (
          <>
            <div style={{
              background: "var(--success-bg)", border: "1px solid var(--success)",
              borderLeft: "3px solid var(--success)", borderRadius: 6, padding: "12px 14px", fontSize: 12,
            }}>
              <div style={{ marginBottom: 8 }}>
                <span style={{ background: "white", padding: "2px 8px", borderRadius: 10, fontSize: 11, color: "var(--success)", fontWeight: 600 }}>
                  {result.verdict === "pass" ? "✓ 通过" : "💭 可以更深"}
                </span>
              </div>
              <div style={{ fontFamily: "var(--font-serif)", lineHeight: 1.65 }}>{result.feedback}</div>
              {result.missing_points.length > 0 && (
                <ul style={{ marginTop: 8, paddingLeft: 16 }}>
                  {result.missing_points.map((p, i) => <li key={i} style={{ color: "var(--text-muted)" }}>{p}</li>)}
                </ul>
              )}
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 14 }}>
              <button onClick={() => setResult(null)} style={subtleBtn}>↩ 再改一次</button>
              <button onClick={confirm} style={primaryBtn}>✓ 收下这个结果</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

const btn: React.CSSProperties = { border: "1px solid var(--border)", background: "var(--surface)", padding: "6px 14px", borderRadius: 6, cursor: "pointer", fontSize: 12 };
const primaryBtn: React.CSSProperties = { ...btn, background: "var(--text)", color: "var(--bg)", borderColor: "var(--text)" };
const subtleBtn: React.CSSProperties = { ...btn, background: "transparent", border: "none", color: "var(--text-muted)" };
