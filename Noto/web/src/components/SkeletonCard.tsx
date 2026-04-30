import { useEffect, useState } from "react";
import { Card, SkeletonNode, cardsApi, skeletonApi } from "../api/client";
import SocraticThread from "./SocraticThread";
import GotItModal from "./GotItModal";

export default function SkeletonCard({ node, notebookId }: { node: SkeletonNode; notebookId: string }) {
  const [card, setCard] = useState<Card | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [showGotIt, setShowGotIt] = useState(false);

  useEffect(() => {
    // Find or create card for this node
    cardsApi.list(notebookId).then(cs => {
      const existing = cs.find(c => c.skeleton_node_id === node.id);
      if (existing) setCard(existing);
    });
  }, [node.id, notebookId]);

  const state = card?.card_state || "unread";

  return (
    <div style={{
      background: state === "thinking" ? "#fffaf4" : state === "got_it" ? "#f7faf5" : state === "stuck" ? "var(--danger-bg)" : "var(--surface)",
      border: `1px solid ${state === "thinking" ? "var(--accent)" : state === "got_it" ? "var(--success)" : state === "stuck" ? "var(--danger)" : "var(--border)"}`,
      borderRadius: 10, padding: "14px 18px", marginBottom: 8,
      cursor: expanded ? "default" : "pointer",
    }} onClick={() => !expanded && setExpanded(true)}>
      <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
        <StateIcon state={state} />
        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: "var(--font-serif)", fontSize: 14, lineHeight: 1.65 }}>
            {node.title}
          </div>
          <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 6, display: "flex", gap: 10 }}>
            <span style={{ color: stateColor(state), fontWeight: 600 }}>{stateLabel(state)}</span>
            {node.source_positions?.[0]?.page_num != null && <span>📖 p.{node.source_positions[0].page_num}</span>}
          </div>

          {expanded && (
            <SocraticThread
              node={node}
              notebookId={notebookId}
              card={card}
              onCardUpdate={setCard}
              onMarkGotIt={async () => {
                if (!card) {
                  const created = await cardsApi.ensureForNode(node.id);
                  setCard(created);
                }
                setShowGotIt(true);
              }}
              onMarkStuck={async () => {
                const c = card || await cardsApi.ensureForNode(node.id);
                await cardsApi.updateState(c.id, { state: "stuck" });
                setCard({ ...c, card_state: "stuck" });
              }}
              onReject={async () => {
                if (confirm("否决这张卡？")) {
                  await skeletonApi.rejectNode(node.id, "用户否决");
                  setExpanded(false);
                }
              }}
              onCollapse={() => setExpanded(false)}
            />
          )}
        </div>
      </div>

      {showGotIt && card && (
        <GotItModal
          node={node}
          card={card}
          onClose={() => setShowGotIt(false)}
          onSuccess={(updated) => { setCard(updated); setShowGotIt(false); }}
        />
      )}
    </div>
  );
}

function StateIcon({ state }: { state: Card["card_state"] }) {
  const common: React.CSSProperties = {
    flexShrink: 0, width: 22, height: 22, borderRadius: "50%",
    display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, marginTop: 1,
  };
  if (state === "unread") return <div style={{ ...common, border: "1.5px solid var(--text-faint)" }} />;
  if (state === "thinking") return <div style={{ ...common, background: "var(--accent-bg)", color: "var(--accent)", fontSize: 11 }}>🤔</div>;
  if (state === "got_it") return <div style={{ ...common, background: "var(--success-bg)", color: "var(--success)" }}>✓</div>;
  return <div style={{ ...common, background: "var(--danger-bg)", color: "var(--danger)" }}>⚠</div>;
}

function stateLabel(s: Card["card_state"]) {
  return s === "unread" ? "未读" : s === "thinking" ? "在想" : s === "got_it" ? "已懂" : "不懂";
}
function stateColor(s: Card["card_state"]) {
  return s === "unread" ? "var(--text-muted)" : s === "thinking" ? "var(--accent)" : s === "got_it" ? "var(--success)" : "var(--danger)";
}
