import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Card, reviewApi } from "../api/client";

export default function ReviewFocus() {
  const [params] = useSearchParams();
  const notebookId = params.get("notebook_id") || "";
  const nav = useNavigate();
  const [queue, setQueue] = useState<Card[]>([]);
  const [idx, setIdx] = useState(0);
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    if (!notebookId) return;
    reviewApi.due(notebookId).then(cs => { setQueue(cs); setIdx(0); });
  }, [notebookId]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") nav(-1);
      else if (e.code === "Space" && !revealed) { e.preventDefault(); setRevealed(true); }
      else if (revealed && ["1", "2", "3", "4"].includes(e.key)) {
        const rating = (["again", "hard", "good", "easy"] as const)[parseInt(e.key) - 1];
        rate(rating);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [revealed, idx, queue]);

  const rate = async (r: "again" | "hard" | "good" | "easy") => {
    const c = queue[idx];
    if (!c) return;
    await reviewApi.rate({ card_id: c.id, rating: r });
    setRevealed(false); setIdx(i => i + 1);
  };

  if (!notebookId) return <Center>缺少 notebook_id 参数<button onClick={() => nav("/")}>返回</button></Center>;
  if (queue.length === 0) return <Center>今天没有到期卡。<button onClick={() => nav(-1)} style={backBtn}>返回</button></Center>;
  if (idx >= queue.length) return <Center>
    <div style={{ fontSize: 48, color: "var(--success)" }}>✓</div>
    <h2 style={{ fontFamily: "var(--font-serif)" }}>复习完成</h2>
    <p>过了 {queue.length} 张卡</p>
    <button onClick={() => nav(-1)} style={{ ...backBtn, marginTop: 16 }}>返回空间首页</button>
  </Center>;

  const c = queue[idx];

  return (
    <div style={{ position: "fixed", inset: 0, background: "var(--bg)", overflowY: "auto" }}>
      <header style={{
        position: "sticky", top: 0, background: "var(--bg)", borderBottom: "1px solid var(--border)",
        padding: "14px 32px", display: "flex", alignItems: "center", gap: 18, zIndex: 10,
      }}>
        <button onClick={() => nav(-1)} style={{ background: "transparent", border: "none", fontSize: 18, cursor: "pointer" }}>←</button>
        <div style={{ fontFamily: "var(--font-serif)", fontWeight: 600 }}>复习</div>
        <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 12, maxWidth: 400 }}>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{idx + 1} / {queue.length}</div>
          <div style={{ flex: 1, height: 4, background: "var(--border)", borderRadius: 2 }}>
            <div style={{ width: `${(idx / queue.length) * 100}%`, height: "100%", background: "var(--accent)" }} />
          </div>
        </div>
        <div style={{ fontSize: 11, color: "var(--text-faint)" }}>
          <span style={kbd}>Space</span> 显示 · <span style={kbd}>1234</span> 评分
        </div>
      </header>

      <div style={{ maxWidth: 720, margin: "0 auto", padding: "40px 32px" }}>
        <div style={{
          background: "var(--surface)", border: "1px solid var(--border)",
          borderRadius: 14, padding: "40px 44px", boxShadow: "var(--shadow-md)",
        }}>
          <div style={{ fontSize: 11, color: "var(--text-faint)", letterSpacing: "0.09em", textTransform: "uppercase", marginBottom: 10 }}>Q</div>
          <div style={{ fontFamily: "var(--font-serif)", fontSize: 20, fontWeight: 600, lineHeight: 1.6, marginBottom: 24 }}>
            {c.question}
          </div>

          {!revealed ? (
            <button onClick={() => setRevealed(true)} style={{
              background: "var(--text)", color: "var(--bg)", padding: "12px 22px", borderRadius: 6,
              border: "none", fontSize: 13, cursor: "pointer",
            }}>显示上次的回答 <span style={{ opacity: 0.6, marginLeft: 8 }}>Space</span></button>
          ) : (
            <>
              <div style={{ height: 1, background: "var(--border)", margin: "24px -44px" }} />
              <div style={{ fontSize: 11, color: "var(--text-faint)", letterSpacing: "0.09em", textTransform: "uppercase", marginBottom: 10 }}>你上次的解释</div>
              <div style={{ fontFamily: "var(--font-serif)", fontSize: 15, lineHeight: 1.85, marginBottom: 18 }}>
                {c.user_explanation || c.answer || "（无历史）"}
              </div>

              <div style={{
                display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginTop: 28,
              }}>
                <RatingBtn label="⚠ again" interval="+1天" onClick={() => rate("again")} border="var(--danger)" />
                <RatingBtn label="😓 hard" interval="+3天" onClick={() => rate("hard")} border="#d4a056" />
                <RatingBtn label="✓ good" interval="+7天" onClick={() => rate("good")} border="var(--success)" />
                <RatingBtn label="🚀 easy" interval="+21天" onClick={() => rate("easy")} border="#5a7a6b" />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function RatingBtn({ label, interval, onClick, border }: { label: string; interval: string; onClick: () => void; border: string }) {
  return (
    <button onClick={onClick} style={{
      padding: "16px 12px", borderRadius: 10,
      border: `1px solid var(--border)`, borderTop: `3px solid ${border}`,
      background: "var(--surface)", cursor: "pointer", display: "flex",
      flexDirection: "column", gap: 4, alignItems: "center",
    }}>
      <div style={{ fontSize: 13, fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: 10, color: "var(--text-muted)" }}>{interval}</div>
    </button>
  );
}

function Center({ children }: { children: React.ReactNode }) {
  return <div style={{
    display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
    minHeight: "100vh", gap: 10,
  }}>{children}</div>;
}

const backBtn: React.CSSProperties = {
  background: "var(--text)", color: "var(--bg)", padding: "8px 16px", borderRadius: 6, border: "none", cursor: "pointer",
};

const kbd: React.CSSProperties = {
  padding: "1px 5px", fontSize: 10, background: "var(--surface)",
  border: "1px solid var(--border)", borderRadius: 3, fontFamily: "var(--font-sans)",
};
