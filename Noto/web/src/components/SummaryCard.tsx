type Props = {
  label: string;
  content: string | null;
  onRegenerate?: () => void;
  disclaimer?: string;
  loading?: boolean;
};

export default function SummaryCard({ label, content, onRegenerate, disclaimer, loading }: Props) {
  return (
    <div style={{
      background: "var(--surface)", border: "1px solid var(--border)",
      borderLeft: "3px solid var(--accent)", borderRadius: 10,
      padding: "22px 28px", marginBottom: 20,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
        <div style={{ fontSize: 11, color: "var(--text-faint)", letterSpacing: "0.09em", textTransform: "uppercase" }}>
          {label}
        </div>
        {onRegenerate && (
          <button onClick={onRegenerate} style={{
            background: "transparent", border: "none", color: "var(--text-muted)",
            fontSize: 11, cursor: "pointer",
          }} disabled={loading}>{loading ? "蒸馏中..." : "重新蒸馏"}</button>
        )}
      </div>
      {disclaimer && (
        <div style={{
          fontSize: 11, color: "var(--text-faint)", fontStyle: "italic",
          paddingBottom: 10, marginBottom: 14, borderBottom: "1px dashed var(--border)",
        }}>{disclaimer}</div>
      )}
      <div style={{
        fontFamily: "var(--font-serif)", fontSize: 14, lineHeight: 1.85,
        whiteSpace: "pre-wrap",
      }}>
        {content || (loading ? "正在蒸馏..." : "还没有概要。")}
      </div>
    </div>
  );
}
