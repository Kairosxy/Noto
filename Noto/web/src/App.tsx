import { useEffect, useState } from "react";
import { BrowserRouter, Route, Routes, Navigate, useNavigate, Link } from "react-router-dom";
import { ConfigProvider } from "./store/config";
import ConfigPage from "./pages/ConfigPage";
import SpaceHomePage from "./pages/SpaceHomePage";
import DocReadingPage from "./pages/DocReadingPage";
import DirectionPage from "./pages/DirectionPage";
import { Notebook, notebooksApi } from "./api/client";

export default function App() {
  return (
    <ConfigProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/space/:id" element={<SpaceHomePage />} />
          <Route path="/doc/:id" element={<DocReadingPage />} />
          <Route path="/direction/:directionId" element={<DirectionPage />} />
          <Route path="/config" element={<ConfigPage />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}

function Home() {
  return <NotebookPicker />;
}

function NotebookPicker() {
  const [items, setItems] = useState<Notebook[]>([]);
  const [title, setTitle] = useState("");
  const [goal, setGoal] = useState("");
  const nav = useNavigate();

  useEffect(() => { notebooksApi.list().then(setItems); }, []);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    const nb = await notebooksApi.create({ title: title.trim(), goal: goal.trim() });
    nav(`/space/${nb.id}`);
  };

  return (
    <div style={{ maxWidth: 640, margin: "60px auto", padding: "0 28px" }}>
      <div style={{ textAlign: "center", marginBottom: 32 }}>
        <img src="/noto-logo.png" alt="Noto" style={{ width: 120, height: "auto", marginBottom: 12 }} />
        <div style={{ fontFamily: "var(--font-serif)", fontSize: 13, color: "var(--text-muted)" }}>
          Notes, without the noise.
        </div>
      </div>

      <div style={{
        background: "var(--surface)", border: "1px solid var(--border)",
        borderRadius: 10, padding: 20, marginBottom: 28,
      }}>
        <h2 style={{ fontFamily: "var(--font-serif)", fontSize: 18, fontWeight: 600, marginBottom: 14 }}>新建学习空间</h2>
        <form onSubmit={create}>
          <label style={{ display: "block", fontSize: 11, color: "var(--text-muted)", marginBottom: 4 }}>主题</label>
          <input value={title} onChange={e => setTitle(e.target.value)} placeholder="例：深度学习第三章"
            style={{ width: "100%", padding: "8px 12px", border: "1px solid var(--border)", borderRadius: 6, marginBottom: 10 }} />
          <label style={{ display: "block", fontSize: 11, color: "var(--text-muted)", marginBottom: 4 }}>学习目标</label>
          <input value={goal} onChange={e => setGoal(e.target.value)} placeholder="例：理解反向传播的数学推导"
            style={{ width: "100%", padding: "8px 12px", border: "1px solid var(--border)", borderRadius: 6, marginBottom: 14 }} />
          <button type="submit" style={{
            background: "var(--text)", color: "var(--bg)", border: "none",
            padding: "8px 16px", borderRadius: 6, cursor: "pointer",
          }}>创建</button>
        </form>
      </div>

      {items.length > 0 && (
        <>
          <div style={{ fontSize: 11, color: "var(--text-faint)", letterSpacing: "0.09em", textTransform: "uppercase", marginBottom: 10 }}>
            我的空间 · {items.length}
          </div>
          {items.map(nb => (
            <div key={nb.id} onClick={() => nav(`/space/${nb.id}`)} style={{
              background: "var(--surface)", border: "1px solid var(--border)",
              borderRadius: 10, padding: 16, marginBottom: 8, cursor: "pointer",
            }}>
              <div style={{ fontFamily: "var(--font-serif)", fontSize: 15, fontWeight: 600 }}>{nb.title}</div>
              {nb.goal && <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 3 }}>{nb.goal}</div>}
            </div>
          ))}
        </>
      )}

      <div style={{ textAlign: "center", marginTop: 32, fontSize: 12, color: "var(--text-muted)" }}>
        <Link to="/config" style={{ color: "var(--text-muted)" }}>⚙ 设置</Link>
      </div>
    </div>
  );
}
