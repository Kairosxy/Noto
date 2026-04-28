import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { notebooksApi, Notebook } from "../api/client";

export default function NotebooksPage() {
  const [items, setItems] = useState<Notebook[]>([]);
  const [title, setTitle] = useState("");
  const [goal, setGoal] = useState("");

  const reload = async () => setItems(await notebooksApi.list());
  useEffect(() => { reload(); }, []);

  const onCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    await notebooksApi.create({ title: title.trim(), goal: goal.trim() });
    setTitle(""); setGoal("");
    await reload();
  };

  return (
    <div>
      <div className="card">
        <h2>新建学习空间</h2>
        <form onSubmit={onCreate}>
          <label>主题</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="例：深度学习第三章" />
          <label>学习目标</label>
          <input value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="例：理解反向传播的数学推导" />
          <button className="primary" type="submit" style={{ marginTop: 8 }}>创建</button>
        </form>
      </div>

      <h2>我的空间</h2>
      {items.length === 0 && <p>还没有空间，上面创建一个。</p>}
      {items.map((n) => (
        <div key={n.id} className="card">
          <Link to={`/notebooks/${n.id}`} style={{ fontSize: 18 }}>{n.title}</Link>
          {n.goal && <p style={{ color: "#666" }}>{n.goal}</p>}
        </div>
      ))}
    </div>
  );
}
