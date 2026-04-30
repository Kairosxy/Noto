import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Document, Notebook, notebooksApi, docsApi, askWithContext, highlightsApi,
} from "../api/client";
import Shell from "../layout/Shell";
import LeftSidebar from "../layout/LeftSidebar";
import RightSidebar from "../layout/RightSidebar";
import Topbar from "../layout/Topbar";
import SummaryCard from "../components/SummaryCard";
import SelectionToolbar from "../components/SelectionToolbar";

type Chunk = { id: string; content: string; page_num: number | null; position: number };

export default function DocReadingPage() {
  const { id } = useParams<{ id: string }>();
  const nav = useNavigate();
  const [doc, setDoc] = useState<Document | null>(null);
  const [notebook, setNotebook] = useState<Notebook | null>(null);
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [selPos, setSelPos] = useState<{ top: number; left: number } | null>(null);
  const [selText, setSelText] = useState("");
  const [selChunkId, setSelChunkId] = useState<string | null>(null);
  const mainRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!id) return;
    (async () => {
      const d = await docsApi.get(id);
      const [sumResp, ch, nb] = await Promise.all([
        docsApi.getSummary(id).catch(() => ({ summary: null })),
        docsApi.getChunks(id),
        notebooksApi.get(d.notebook_id),
      ]);
      setDoc({ ...d, summary: sumResp.summary });
      setChunks(ch);
      setNotebook(nb);
    })();
  }, [id]);

  const onMouseUp = () => {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) { setSelPos(null); return; }
    const range = sel.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    const mainRect = mainRef.current?.getBoundingClientRect();
    if (!mainRect) return;
    setSelText(sel.toString());
    setSelPos({ top: rect.top - mainRect.top - 40, left: rect.left - mainRect.left });
    let node: Node | null = range.startContainer;
    while (node) {
      if ((node as HTMLElement).dataset?.chunkId) {
        setSelChunkId((node as HTMLElement).dataset.chunkId!);
        break;
      }
      node = node.parentNode;
    }
  };

  const doAction = async (action: "ask" | "mark_stuck" | "save_note") => {
    if (!doc || !notebook) return;
    const q = action === "ask" ? (prompt("你要问什么？") || "") : "";
    await askWithContext({
      notebook_id: notebook.id,
      document_id: doc.id,
      chunk_id: selChunkId || undefined,
      selected_text: selText,
      user_question: q,
      action,
    });
    setSelPos(null); window.getSelection()?.removeAllRanges();
    alert(action === "ask" ? "已为选中段创建问题卡" : action === "mark_stuck" ? "已标为不懂" : "已保存笔记");
  };

  const onHighlight = async () => {
    if (!doc || !selText) return;
    await highlightsApi.create({
      document_id: doc.id,
      chunk_id: selChunkId || undefined,
      text: selText,
    });
    setSelPos(null); window.getSelection()?.removeAllRanges();
  };

  if (!doc || !notebook) return <div style={{padding:40}}>Loading...</div>;

  return (
    <Shell
      sidebar={<LeftSidebar />}
      topbar={<Topbar mode="doc" notebookId={notebook.id} notebookTitle={notebook.title}
        docTitle={doc.filename} docPages={doc.pages}
        stats={{ got_it: 0, thinking: 0, stuck: 0 }} />}
      rightbar={<RightSidebar notebookId={notebook.id} />}
      main={
        <div ref={mainRef} onMouseUp={onMouseUp} style={{ position: "relative" }}>
          <div style={{ marginBottom: 14 }}>
            <button onClick={() => nav(`/space/${notebook.id}`)} style={{
              background: "transparent", border: "none", color: "var(--text-muted)",
              fontSize: 12, cursor: "pointer",
            }}>← 返回空间首页</button>
          </div>

          <SummaryCard
            label={`📄 概要 · ${doc.filename}`}
            content={doc.summary}
            onRegenerate={async () => { await docsApi.regenerateSummary(doc.id); window.location.reload(); }}
          />

          <div style={{
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: 10, overflow: "hidden",
          }}>
            <div style={{ padding: "10px 18px", borderBottom: "1px solid var(--border)", fontSize: 11, color: "var(--text-muted)" }}>
              📑 原文 · {doc.pages ?? chunks.length} 段
            </div>
            <div style={{ padding: "28px 36px 38px", fontFamily: "var(--font-serif)", fontSize: 15, lineHeight: 1.95 }}>
              {chunks.map((c) => (
                <p key={c.id} data-chunk-id={c.id} style={{ marginBottom: 14 }}>
                  {c.content}
                  {c.page_num != null && <span style={{ color: "var(--text-faint)", fontSize: 11, marginLeft: 8, fontFamily: "var(--font-sans)" }}>[p.{c.page_num}]</span>}
                </p>
              ))}
            </div>
          </div>

          <SelectionToolbar
            position={selPos}
            onAsk={() => doAction("ask")}
            onMarkStuck={() => doAction("mark_stuck")}
            onHighlight={onHighlight}
            onSaveNote={() => doAction("save_note")}
          />
        </div>
      }
    />
  );
}
