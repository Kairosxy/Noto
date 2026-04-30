import { LearningDirection } from "../api/client";

export default function DirectionCard({
  direction, cardCount, masteredCount, onOpen,
}: {
  direction: LearningDirection;
  cardCount: number;
  masteredCount: number;
  onOpen: () => void;
}) {
  const progress = cardCount > 0 ? Math.round((masteredCount / cardCount) * 100) : 0;

  return (
    <div onClick={onOpen} style={{
      background: "var(--surface)", border: "1px solid var(--border)",
      borderRadius: 10, padding: "16px 20px", marginBottom: 10, cursor: "pointer",
      display: "flex", alignItems: "center", gap: 16,
    }}>
      <div style={{
        width: 32, height: 32, borderRadius: "50%",
        background: "var(--accent-bg)", color: "var(--accent)",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontFamily: "var(--font-serif)", fontWeight: 600, fontSize: 15,
      }}>{direction.position + 1}</div>

      <div style={{ flex: 1 }}>
        <div style={{ fontFamily: "var(--font-serif)", fontSize: 15, fontWeight: 600, marginBottom: 4 }}>
          {direction.title}
        </div>
        <div style={{ fontSize: 12, color: "var(--text-muted)", lineHeight: 1.55, marginBottom: 6 }}>
          {direction.description}
        </div>
        <div style={{ fontSize: 11, color: "var(--text-faint)", display: "flex", gap: 10 }}>
          <span>{cardCount} 张卡 · 约 {direction.estimated_minutes ?? 10} 分钟</span>
          <span>懂 {masteredCount}/{cardCount}</span>
          <span style={{ width: 80, height: 3, background: "var(--border)", borderRadius: 2, display: "inline-block", alignSelf: "center" }}>
            <span style={{ display: "block", height: "100%", width: `${progress}%`, background: "var(--success)", borderRadius: 2 }} />
          </span>
        </div>
      </div>

      <div style={{ color: "var(--accent)" }}>→</div>
    </div>
  );
}
