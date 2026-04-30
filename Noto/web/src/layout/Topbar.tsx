import { Link } from "react-router-dom";

type Stats = { got_it: number; thinking: number; stuck: number; streak_days?: number };

export default function Topbar({
  mode, notebookId, notebookTitle, goal,
  docTitle, docPages, stats,
  onReview,
}: {
  mode: "space" | "doc";
  notebookId: string;
  notebookTitle: string;
  goal?: string;
  docTitle?: string;
  docPages?: number | null;
  stats: Stats;
  onReview?: () => void;
}) {
  return (
    <header style={{
      background: "var(--bg)", borderBottom: "1px solid var(--border)",
      padding: "12px 28px", display: "flex", alignItems: "center", gap: 14,
      position: "sticky", top: 0, zIndex: 10,
    }}>
      {mode === "space" ? (
        <>
          <div style={{ fontFamily: "var(--font-serif)", fontSize: 16, fontWeight: 600 }}>{notebookTitle}</div>
          {goal && <><span style={{ color: "var(--border)" }}>·</span>
            <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{goal}</div></>}
        </>
      ) : (
        <>
          <Link to={`/space/${notebookId}`} style={{ fontSize: 12, color: "var(--text-muted)" }}>{notebookTitle}</Link>
          <span style={{ color: "var(--border)" }}>›</span>
          <div style={{ fontFamily: "var(--font-serif)", fontSize: 16, fontWeight: 600 }}>{docTitle}</div>
          {docPages != null && <>
            <span style={{ color: "var(--border)" }}>·</span>
            <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{docPages} 页</div>
          </>}
        </>
      )}

      <div style={{ marginLeft: "auto", display: "flex", gap: 14, fontSize: 12, color: "var(--text-muted)" }}>
        <span>懂 <b style={{ color: "var(--text)" }}>{stats.got_it}</b></span>
        <span>在想 <b style={{ color: "var(--accent)" }}>{stats.thinking}</b></span>
        <span>不懂 <b style={{ color: "var(--danger)" }}>{stats.stuck}</b></span>
        {stats.streak_days != null && <span>🔥 {stats.streak_days} 天</span>}
      </div>

      {onReview && (
        <button onClick={onReview} style={{
          border: "1px solid var(--border)", background: "var(--surface)", padding: "6px 12px",
          borderRadius: 6, fontSize: 12, color: "var(--text)", cursor: "pointer",
        }}>🔁 复习</button>
      )}
    </header>
  );
}
