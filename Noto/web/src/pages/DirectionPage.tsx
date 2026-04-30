import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { Notebook, Skeleton, notebooksApi, skeletonApi } from "../api/client";
import Shell from "../layout/Shell";
import LeftSidebar from "../layout/LeftSidebar";
import RightSidebar from "../layout/RightSidebar";
import Topbar from "../layout/Topbar";
import SkeletonCard from "../components/SkeletonCard";

export default function DirectionPage() {
  const { directionId } = useParams<{ directionId: string }>();
  const [params] = useSearchParams();
  const queryNotebookId = params.get("notebook_id");
  const nav = useNavigate();
  const [skeleton, setSkeleton] = useState<Skeleton | null>(null);
  const [notebook, setNotebook] = useState<Notebook | null>(null);

  useEffect(() => {
    (async () => {
      if (queryNotebookId) {
        const [sk, nb] = await Promise.all([
          skeletonApi.get(queryNotebookId),
          notebooksApi.get(queryNotebookId),
        ]);
        setSkeleton(sk); setNotebook(nb);
      } else {
        // Fall back: search all notebooks for the direction (slower but robust)
        const notebooks = await notebooksApi.list();
        for (const nb of notebooks) {
          const sk = await skeletonApi.get(nb.id);
          if (sk.directions?.some(d => d.id === directionId)) {
            setSkeleton(sk); setNotebook(nb); break;
          }
        }
      }
    })();
  }, [directionId, queryNotebookId]);

  if (!skeleton || !notebook) return <div style={{padding:40}}>Loading...</div>;
  const dir = skeleton.directions.find(d => d.id === directionId);
  if (!dir) return <div style={{padding:40}}>方向不存在</div>;
  const nodes = skeleton.nodes.filter(n => dir.node_ids.includes(n.id));
  const claims = nodes.filter(n => n.node_type === "claim");
  const concepts = nodes.filter(n => n.node_type === "concept");
  const questions = nodes.filter(n => n.node_type === "question");

  return (
    <Shell
      sidebar={<LeftSidebar />}
      topbar={<Topbar mode="doc" notebookId={notebook.id} notebookTitle={notebook.title}
        docTitle={dir.title} stats={{ got_it: 0, thinking: 0, stuck: 0 }} />}
      rightbar={<RightSidebar notebookId={notebook.id} />}
      main={
        <>
          <div style={{ marginBottom: 18 }}>
            <button onClick={() => nav(`/space/${notebook.id}`)} style={{
              background: "transparent", border: "none", color: "var(--text-muted)", fontSize: 12, cursor: "pointer",
            }}>← 返回学习方向</button>
          </div>

          <h1 style={{ fontFamily: "var(--font-serif)", fontSize: 24, fontWeight: 600, marginBottom: 4 }}>{dir.title}</h1>
          <div style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 24 }}>
            {dir.description} · 预计 {dir.estimated_minutes ?? 10} 分钟
          </div>

          <CardGroup title="核心主张" count={claims.length}>
            {claims.map(n => <SkeletonCard key={n.id} node={n} notebookId={notebook.id} />)}
          </CardGroup>

          <CardGroup title="关键概念" count={concepts.length}>
            {concepts.map(n => <SkeletonCard key={n.id} node={n} notebookId={notebook.id} />)}
          </CardGroup>

          <CardGroup title="Noto 建议你思考" count={questions.length}>
            {questions.map(n => <SkeletonCard key={n.id} node={n} notebookId={notebook.id} />)}
          </CardGroup>
        </>
      }
    />
  );
}

function CardGroup({ title, count, children }: { title: string; count: number; children: React.ReactNode }) {
  if (count === 0) return null;
  return (
    <div style={{ marginBottom: 22 }}>
      <div style={{
        fontSize: 11, color: "var(--text-faint)", letterSpacing: "0.09em",
        textTransform: "uppercase", marginBottom: 10,
      }}>{title} · {count}</div>
      {children}
    </div>
  );
}
