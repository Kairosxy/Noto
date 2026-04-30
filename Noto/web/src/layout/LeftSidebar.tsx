import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { notebooksApi, Notebook } from "../api/client";

export default function LeftSidebar() {
  const [items, setItems] = useState<Notebook[]>([]);
  const loc = useLocation();

  useEffect(() => { notebooksApi.list().then(setItems); }, []);

  return (
    <>
      <div style={{ display: "flex", justifyContent: "center", marginBottom: 22, padding: "6px 0" }}>
        <Link to="/"><img src="/noto-logo.png" alt="Noto" style={{ width: 88, height: "auto" }} /></Link>
      </div>

      <div style={{ fontSize: 10, color: "var(--text-faint)", letterSpacing: "0.09em", textTransform: "uppercase", marginBottom: 8, padding: "0 4px" }}>
        学习空间
      </div>

      {items.map((nb) => {
        const active = loc.pathname.startsWith(`/space/${nb.id}`);
        return (
          <Link
            key={nb.id}
            to={`/space/${nb.id}`}
            style={{
              display: "flex", alignItems: "center", gap: 8,
              padding: "8px 10px", borderRadius: 6,
              fontFamily: "var(--font-serif)", fontSize: 13,
              color: active ? "var(--text)" : "var(--text-muted)",
              background: active ? "var(--border)" : "transparent",
              marginBottom: 2,
            }}
          >
            {active && <span style={{ width: 5, height: 5, background: "var(--accent)", borderRadius: "50%" }} />}
            <span>{nb.title}</span>
          </Link>
        );
      })}

      <Link to="/" style={{
        color: "var(--text-faint)", fontFamily: "var(--font-serif)",
        fontSize: 13, padding: "8px 10px", display: "block",
      }}>+ 新建空间</Link>

      <div style={{
        marginTop: "auto", paddingTop: 14, borderTop: "1px solid var(--border)",
        fontSize: 12, color: "var(--text-muted)", display: "flex", gap: 12,
      }}>
        <Link to="/config">⚙ 设置</Link>
      </div>
    </>
  );
}
