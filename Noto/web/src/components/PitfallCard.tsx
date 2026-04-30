import { SkeletonNode } from "../api/client";

export default function PitfallCard({ node }: { node: SkeletonNode }) {
  return (
    <div style={{
      background: "var(--surface)", border: "1px solid var(--border)",
      borderRadius: 10, padding: "12px 16px", fontSize: 13, lineHeight: 1.55,
      cursor: "pointer",
    }}>
      <div style={{ fontSize: 10, color: "var(--accent)", fontWeight: 600, marginBottom: 4 }}>⚠ 误解</div>
      <div style={{ fontFamily: "var(--font-serif)", color: "var(--text)" }}>{node.title}</div>
      {node.body && <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 3 }}>{node.body}</div>}
    </div>
  );
}
