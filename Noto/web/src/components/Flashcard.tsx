import { useState } from "react";
import { Card, reviewApi } from "../api/client";

const RATINGS = ["again", "hard", "good", "easy"] as const;

export default function Flashcard({ card, onDone }: { card: Card; onDone: () => void }) {
  const [shown, setShown] = useState(false);

  const rate = async (r: (typeof RATINGS)[number]) => {
    await reviewApi.rate({ card_id: card.id, rating: r });
    setShown(false);
    onDone();
  };

  return (
    <div className="card">
      <p style={{ fontSize: 18 }}><strong>Q：</strong>{card.question}</p>
      {shown ? (
        <>
          <p><strong>A：</strong>{card.answer}</p>
          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            {RATINGS.map((r) => (
              <button key={r} onClick={() => rate(r)}>{r}</button>
            ))}
          </div>
        </>
      ) : (
        <button className="primary" onClick={() => setShown(true)}>显示答案</button>
      )}
    </div>
  );
}
