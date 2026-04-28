import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Card, reviewApi } from "../api/client";
import Flashcard from "../components/Flashcard";

export default function ReviewSession() {
  const { id } = useParams<{ id: string }>();
  const [queue, setQueue] = useState<Card[]>([]);
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    if (!id) return;
    reviewApi.due(id).then((cs) => { setQueue(cs); setIdx(0); });
  }, [id]);

  if (!id) return null;
  if (queue.length === 0) return (
    <div className="card">
      今天没有到期卡，回到 <Link to={`/notebooks/${id}`}>空间</Link>。
    </div>
  );
  if (idx >= queue.length) return <div className="card">✅ 全部完成（{queue.length} 张）</div>;

  return (
    <div>
      <p style={{ color: "#666" }}>复习 {idx + 1} / {queue.length}</p>
      <Flashcard card={queue[idx]} onDone={() => setIdx(idx + 1)} />
    </div>
  );
}
