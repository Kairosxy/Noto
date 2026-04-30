import { Card } from "../api/client";

export default function NoteListItem({ card }: { card: Card }) {
  const color = card.card_state === "got_it" ? "var(--success)"
    : card.card_state === "thinking" ? "var(--accent)"
    : card.card_state === "stuck" ? "var(--danger)"
    : "var(--text-muted)";
  const stateText = card.card_state === "got_it" ? "已懂"
    : card.card_state === "thinking" ? "🤔 在想"
    : card.card_state === "stuck" ? "⚠ 不懂"
    : "未读";

  return (
    <div style={{
      background: "var(--surface)", border: "1px solid var(--border)",
      borderRadius: 6, padding: "10px 12px", marginBottom: 6, cursor: "pointer",
    }}>
      <div style={{ fontFamily: "var(--font-serif)", fontSize: 13, fontWeight: 500, color: "var(--text)", marginBottom: 3 }}>
        {card.question}
      </div>
      <div style={{ fontSize: 10, color, fontFamily: "var(--font-sans)" }}>{stateText}</div>
    </div>
  );
}
