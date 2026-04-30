import { useEffect, useState } from "react";
import { Card, cardsApi } from "../api/client";
import NoteListItem from "../components/NoteListItem";

export default function RightSidebar({ notebookId }: { notebookId: string }) {
  const [cards, setCards] = useState<Card[]>([]);
  useEffect(() => { cardsApi.list(notebookId).then(setCards); }, [notebookId]);

  return (
    <>
      <div style={{
        fontSize: 10, color: "var(--text-faint)", letterSpacing: "0.09em",
        textTransform: "uppercase", marginBottom: 10,
      }}>
        📝 我的知识点 · {cards.length}
      </div>
      {cards.length === 0 && <div style={{ fontSize: 12, color: "var(--text-faint)" }}>读文档时会在这里累积笔记。</div>}
      {cards.map((c) => <NoteListItem key={c.id} card={c} />)}
    </>
  );
}
