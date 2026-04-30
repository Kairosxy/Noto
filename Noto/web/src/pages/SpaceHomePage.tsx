import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Document, Notebook, Skeleton, notebooksApi, skeletonApi, uploadDocument, Card, cardsApi,
} from "../api/client";
import Shell from "../layout/Shell";
import LeftSidebar from "../layout/LeftSidebar";
import RightSidebar from "../layout/RightSidebar";
import Topbar from "../layout/Topbar";
import SummaryCard from "../components/SummaryCard";
import DocSquareCard from "../components/DocSquareCard";
import DirectionCard from "../components/DirectionCard";
import PitfallCard from "../components/PitfallCard";

export default function SpaceHomePage() {
  const { id } = useParams<{ id: string }>();
  const nav = useNavigate();
  const [notebook, setNotebook] = useState<Notebook | null>(null);
  const [docs, setDocs] = useState<Document[]>([]);
  const [skeleton, setSkeleton] = useState<Skeleton | null>(null);
  const [cards, setCards] = useState<Card[]>([]);
  const [regenerating, setRegenerating] = useState(false);

  const reload = async () => {
    if (!id) return;
    const [nb, ds, sk, cs] = await Promise.all([
      notebooksApi.get(id),
      notebooksApi.listDocuments(id),
      skeletonApi.get(id),
      cardsApi.list(id),
    ]);
    setNotebook(nb); setDocs(ds); setSkeleton(sk); setCards(cs);
  };

  useEffect(() => { reload(); }, [id]);
  useEffect(() => {
    const t = setInterval(() => {
      if (docs.some((d) => d.status === "parsing") || skeleton?.status === "generating") reload();
    }, 3000);
    return () => clearInterval(t);
  }, [docs, skeleton]);

  const onRegenerate = async () => {
    if (!id) return;
    setRegenerating(true);
    await skeletonApi.regenerate(id);
    setTimeout(() => { setRegenerating(false); reload(); }, 1500);
  };

  if (!id || !notebook) return <div style={{padding:40}}>Loading...</div>;

  const pitfalls = (skeleton?.nodes || []).filter(n => n.node_type === "pitfall");
  const stats = {
    got_it: cards.filter(c => c.card_state === "got_it").length,
    thinking: cards.filter(c => c.card_state === "thinking").length,
    stuck: cards.filter(c => c.card_state === "stuck").length,
  };

  return (
    <Shell
      sidebar={<LeftSidebar />}
      topbar={<Topbar mode="space" notebookId={id} notebookTitle={notebook.title} goal={notebook.goal}
        stats={stats}
        onReview={() => nav(`/review?notebook_id=${id}`)} />}
      rightbar={<RightSidebar notebookId={id} />}
      main={
        <>
          <SummaryCard
            label="📄 空间概要"
            content={skeleton?.space_summary || null}
            disclaimer="这是 AI 整理的阅读草稿 · 发现不对可以质疑 / 修改 / 删除"
            onRegenerate={onRegenerate}
            loading={regenerating || skeleton?.status === "generating"}
          />

          <SectionHeader>📚 学习资料 · {docs.length} 份</SectionHeader>
          <div style={{
            display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(210px, 1fr))", gap: 12, marginBottom: 24,
          }}>
            {docs.map(d => (
              <DocSquareCard key={d.id} doc={d} onClick={() => nav(`/doc/${d.id}`)} />
            ))}
            <UploadPlaceholder notebookId={id} onUploaded={reload} />
          </div>

          {skeleton?.directions && skeleton.directions.length > 0 && (
            <>
              <SectionHeader>🎯 学习方向 · {skeleton.directions.length}</SectionHeader>
              {skeleton.directions.map(d => (
                <DirectionCard
                  key={d.id} direction={d}
                  cardCount={d.node_ids.length}
                  masteredCount={0}
                  onOpen={() => nav(`/direction/${d.id}?notebook_id=${id}`)}
                />
              ))}
            </>
          )}

          {pitfalls.length > 0 && (
            <>
              <SectionHeader>⚠ 常见误解 · {pitfalls.length}</SectionHeader>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 24 }}>
                {pitfalls.map(p => <PitfallCard key={p.id} node={p} />)}
              </div>
            </>
          )}
        </>
      }
    />
  );
}

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      fontSize: 11, color: "var(--text-faint)", letterSpacing: "0.09em",
      textTransform: "uppercase", margin: "22px 0 12px", display: "flex", alignItems: "center", gap: 6,
    }}>
      <span style={{ width: 4, height: 4, background: "var(--accent)", borderRadius: "50%" }} />
      {children}
    </div>
  );
}

function UploadPlaceholder({ notebookId, onUploaded }: { notebookId: string; onUploaded: () => void }) {
  const [busy, setBusy] = useState(false);
  const handleFile = async (f: File) => {
    setBusy(true);
    try {
      await uploadDocument(notebookId, f);
      onUploaded();
    } finally { setBusy(false); }
  };

  return (
    <label style={{
      background: "transparent", border: "1px dashed var(--text-faint)",
      borderRadius: 10, padding: "22px", display: "flex", flexDirection: "column",
      alignItems: "center", gap: 4, cursor: "pointer", minHeight: 200, justifyContent: "center",
    }}>
      <div style={{ fontSize: 32, color: "var(--text-faint)", fontFamily: "var(--font-serif)", fontWeight: 300 }}>+</div>
      <div style={{ fontFamily: "var(--font-serif)", fontSize: 14, color: "var(--text-muted)" }}>
        {busy ? "上传中..." : "上传新文档"}
      </div>
      <div style={{ fontSize: 11, color: "var(--text-faint)" }}>PDF / MD / TXT</div>
      <input type="file" accept=".pdf,.txt,.md,.docx" style={{ display: "none" }}
        disabled={busy} onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])} />
    </label>
  );
}
