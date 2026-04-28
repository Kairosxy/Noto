import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Document, Notebook, notebooksApi } from "../api/client";
import ChatView from "../components/ChatView";
import ReportView from "../components/ReportView";
import UploadZone from "../components/UploadZone";

type Tab = "docs" | "chat" | "review" | "report";

export default function NotebookDetail() {
  const { id } = useParams<{ id: string }>();
  const [nb, setNb] = useState<Notebook | null>(null);
  const [docs, setDocs] = useState<Document[]>([]);
  const [tab, setTab] = useState<Tab>("docs");
  const docsRef = useRef<Document[]>([]);
  docsRef.current = docs;

  const reload = async () => {
    if (!id) return;
    setNb(await notebooksApi.get(id));
    setDocs(await notebooksApi.listDocuments(id));
  };

  useEffect(() => {
    reload();
    const t = setInterval(() => {
      if (docsRef.current.some((d) => d.status === "parsing")) reload();
    }, 3000);
    return () => clearInterval(t);
  }, [id]);

  if (!id || !nb) return <div>加载中...</div>;

  return (
    <div>
      <div className="card">
        <h1>{nb.title}</h1>
        <p style={{ color: "#666" }}>{nb.goal}</p>
      </div>

      <nav style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        {(["docs", "chat", "review", "report"] as Tab[]).map((t) => (
          <button key={t} className={tab === t ? "primary" : ""} onClick={() => setTab(t)}>
            {t === "docs" ? "资料" : t === "chat" ? "对话" : t === "review" ? "复习" : "报告"}
          </button>
        ))}
      </nav>

      {tab === "docs" && (
        <div>
          <UploadZone notebookId={id} onUploaded={reload} />
          {docs.map((d) => (
            <div key={d.id} className="card">
              <strong>{d.filename}</strong>
              <span style={{ marginLeft: 8, color: "#888" }}>{d.status}</span>
            </div>
          ))}
        </div>
      )}
      {tab === "chat" && <ChatView notebookId={id} />}
      {tab === "review" && (
        <div className="card">
          <Link to={`/notebooks/${id}/review`}>
            <button className="primary">开始复习到期卡</button>
          </Link>
        </div>
      )}
      {tab === "report" && <ReportView notebookId={id} />}
    </div>
  );
}
