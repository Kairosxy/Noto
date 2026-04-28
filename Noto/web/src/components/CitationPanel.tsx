type Citation = { chunk_id: string; page_num: number | null };

export default function CitationPanel({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) return <div style={{ color: "#999" }}>（无引用）</div>;
  return (
    <div>
      <h3 style={{ fontSize: 14 }}>本轮引用</h3>
      {citations.map((c, i) => (
        <div key={c.chunk_id} className="card" style={{ padding: 8, fontSize: 12 }}>
          #{i + 1} {c.page_num != null && `p.${c.page_num}`}
          <div style={{ color: "#666" }}>chunk: {c.chunk_id.slice(0, 8)}</div>
        </div>
      ))}
    </div>
  );
}
