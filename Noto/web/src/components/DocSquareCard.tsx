import { Document } from "../api/client";

export default function DocSquareCard({
  doc, stats, onClick,
}: {
  doc: Document;
  stats?: { got_it: number; thinking: number; stuck: number; total: number };
  onClick: () => void;
}) {
  const summaryPreview = (doc.summary || "").split("\n")
    .filter(line => !line.startsWith("#") && line.trim())
    .join(" ").slice(0, 100);

  return (
    <div onClick={onClick} style={{
      background: "var(--surface)", border: "1px solid var(--border)",
      borderRadius: 10, padding: "14px 16px 12px", cursor: "pointer",
      display: "flex", flexDirection: "column", minHeight: 200,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <span style={{ fontSize: 18 }}>📄</span>
        <span style={{
          fontSize: 10, color: "var(--text-faint)", background: "var(--bg-drawer)",
          padding: "2px 8px", borderRadius: 10,
        }}>{doc.mime?.includes("pdf") ? "PDF" : "DOC"} · {doc.pages ?? "?"} 页</span>
      </div>
      <div style={{
        fontFamily: "var(--font-serif)", fontSize: 14, fontWeight: 600,
        lineHeight: 1.4, marginBottom: 6,
      }}>{doc.filename}</div>
      <div style={{
        fontFamily: "var(--font-serif)", fontSize: 12, lineHeight: 1.65,
        color: "var(--text-muted)", flex: 1,
        display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden",
        marginBottom: 10,
      }}>{summaryPreview || (doc.status === "ready" ? "（等待生成概要）" : `（${doc.status}）`)}</div>

      {stats && (
        <>
          <div style={{ height: 3, background: "var(--border)", borderRadius: 2, marginBottom: 6 }}>
            <div style={{
              height: "100%",
              width: `${stats.total ? (stats.got_it / stats.total) * 100 : 0}%`,
              background: "var(--success)",
            }} />
          </div>
          <div style={{ display: "flex", gap: 8, fontSize: 10, color: "var(--text-muted)" }}>
            <span>懂 <b style={{ color: "var(--text)" }}>{stats.got_it}</b></span>
            <span style={{ color: "var(--accent)" }}>在想 {stats.thinking}</span>
            <span style={{ color: "var(--danger)" }}>不懂 {stats.stuck}</span>
          </div>
        </>
      )}
    </div>
  );
}
