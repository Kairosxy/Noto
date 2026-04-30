export default function SelectionToolbar({
  position, onAsk, onMarkStuck, onHighlight, onSaveNote,
}: {
  position: { top: number; left: number } | null;
  onAsk: () => void;
  onMarkStuck: () => void;
  onHighlight: () => void;
  onSaveNote: () => void;
}) {
  if (!position) return null;
  return (
    <div style={{
      position: "absolute", top: position.top, left: position.left,
      display: "inline-flex", gap: 2, background: "var(--text)", color: "var(--bg)",
      borderRadius: 6, padding: "5px 6px", fontSize: 11,
      boxShadow: "0 6px 16px rgba(0,0,0,0.25)", zIndex: 50,
    }}>
      <button onClick={onAsk} style={btnStyle}>🎯 问 AI</button>
      <span style={sepStyle}>·</span>
      <button onClick={onMarkStuck} style={btnStyle}>⚠ 标记不懂</button>
      <span style={sepStyle}>·</span>
      <button onClick={onHighlight} style={btnStyle}>🖍 高亮</button>
      <span style={sepStyle}>·</span>
      <button onClick={onSaveNote} style={btnStyle}>📝 保存笔记</button>
    </div>
  );
}
const btnStyle: React.CSSProperties = { background: "transparent", color: "inherit", border: "none", padding: "3px 8px", cursor: "pointer", fontSize: 11 };
const sepStyle: React.CSSProperties = { color: "#4a413a", padding: "3px 0" };
