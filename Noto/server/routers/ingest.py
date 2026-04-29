"""文档上传 + 解析 + 嵌入"""

import asyncio
import logging
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Request, UploadFile

from services.ai.embedding import embed
from services.document import chunk, parse

log = logging.getLogger("noto.ingest")

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


@router.post("/upload")
async def upload(
    request: Request,
    background: BackgroundTasks,
    notebook_id: str = Form(...),
    file: UploadFile = File(...),
):
    supa = request.app.state.supabase.client
    cfg = request.app.state.config

    content = await file.read()
    doc_id = str(uuid.uuid4())
    ext = Path(file.filename or "").suffix.lower()
    path = f"{notebook_id}/{doc_id}{ext}"
    supa.storage.from_("documents").upload(path, content, {"content-type": file.content_type or "application/octet-stream"})

    supa.table("documents").insert({
        "id": doc_id,
        "notebook_id": notebook_id,
        "filename": file.filename,
        "storage_path": path,
        "mime": file.content_type,
        "status": "parsing",
    }).execute()

    background.add_task(_process_document, cfg, supa, doc_id, content, ext or ".txt", request.app.state.ai_manager)

    return {"document_id": doc_id, "status": "parsing"}


async def _process_document(cfg, supa, doc_id: str, content: bytes, ext: str, ai_manager):
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        doc = parse(tmp_path)
        chunks = chunk(doc, target_tokens=800)

        eff = cfg.effective_embedding()
        if not eff["model"]:
            raise RuntimeError("embedding model 未配置")

        vectors = await embed(
            texts=[c.content for c in chunks],
            provider=eff["provider"],
            api_key=eff["api_key"],
            base_url=eff["base_url"],
            model=eff["model"],
        )

        rows = [
            {
                "document_id": doc_id,
                "content": c.content,
                "page_num": c.page_num,
                "position": c.position,
                "embedding": vec,
            }
            for c, vec in zip(chunks, vectors)
        ]
        if rows:
            supa.table("chunks").insert(rows).execute()

        supa.table("documents").update({
            "pages": doc.pages,
            "status": "ready",
        }).eq("id", doc_id).execute()

        # === v2 additions ===
        # Generate doc summary
        try:
            from services.distill import distill_doc_summary
            full_text = "\n\n".join(c.content for c in chunks)[:60000]
            summary_md = await distill_doc_summary(
                manager=ai_manager,
                document_text=full_text,
            )
            supa.table("documents").update({"summary": summary_md}).eq("id", doc_id).execute()
        except Exception as e:
            log.warning("doc summary distill failed: %s", e)

        # Re-distill space skeleton (considering all ready docs including this one)
        try:
            nb_id_result = supa.table("documents").select("notebook_id").eq("id", doc_id).single().execute()
            nb_id = nb_id_result.data["notebook_id"]
            nb = supa.table("notebooks").select("goal").eq("id", nb_id).single().execute()
            goal = nb.data.get("goal", "") if nb.data else ""
            ready_docs = supa.table("documents").select("id,filename,summary").eq("notebook_id", nb_id).eq("status", "ready").execute()
            docs_summaries = [
                {"document_id": d["id"], "title": d["filename"], "summary": d.get("summary") or ""}
                for d in (ready_docs.data or [])
                if d.get("summary")
            ]
            if docs_summaries:
                from routers.skeleton import _run_skeleton_distill
                existing = supa.table("skeletons").select("id").eq("notebook_id", nb_id).maybe_single().execute()
                if existing.data:
                    skeleton_id = existing.data["id"]
                    supa.table("skeletons").update({"status": "generating"}).eq("id", skeleton_id).execute()
                else:
                    r = supa.table("skeletons").insert({"notebook_id": nb_id, "status": "generating"}).execute()
                    skeleton_id = r.data[0]["id"]
                await asyncio.to_thread(_run_skeleton_distill, ai_manager, supa, skeleton_id, nb_id, goal, docs_summaries)
        except Exception as e:
            log.warning("space skeleton redistill after doc upload failed: %s", e)

    except Exception:
        log.exception("文档解析失败 doc_id=%s", doc_id)
        supa.table("documents").update({"status": "failed"}).eq("id", doc_id).execute()


@router.get("/document/{doc_id}")
async def get_document(doc_id: str, request: Request):
    supa = request.app.state.supabase.client
    r = supa.table("documents").select("*").eq("id", doc_id).single().execute()
    if not r.data:
        raise HTTPException(404)
    return r.data


@router.get("/document/{doc_id}/summary")
async def get_document_summary(doc_id: str, request: Request):
    supa = request.app.state.supabase.client
    r = supa.table("documents").select("id,summary").eq("id", doc_id).single().execute()
    if not r.data:
        raise HTTPException(404)
    return {"document_id": r.data["id"], "summary": r.data.get("summary")}


@router.post("/document/{doc_id}/summary/regenerate")
async def regenerate_document_summary(doc_id: str, request: Request):
    supa = request.app.state.supabase.client
    mgr = request.app.state.ai_manager
    if not mgr.is_configured:
        raise HTTPException(400, "AI 未配置")

    chunks = supa.table("chunks").select("content").eq("document_id", doc_id).order("position").execute()
    if not chunks.data:
        raise HTTPException(400, "文档还没有切块或未就绪")

    full_text = "\n\n".join(c["content"] for c in chunks.data)[:60000]
    from services.distill import distill_doc_summary
    summary = await distill_doc_summary(mgr, full_text)
    supa.table("documents").update({"summary": summary}).eq("id", doc_id).execute()
    return {"document_id": doc_id, "summary": summary}


@router.get("/document/{doc_id}/chunks")
async def get_document_chunks(doc_id: str, request: Request):
    supa = request.app.state.supabase.client
    r = supa.table("chunks").select("id,content,page_num,position").eq("document_id", doc_id).order("position").execute()
    return r.data or []
