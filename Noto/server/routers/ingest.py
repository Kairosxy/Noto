"""文档上传 + 解析 + 嵌入"""

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

    # 1. 上传到 Storage
    content = await file.read()
    doc_id = str(uuid.uuid4())
    ext = Path(file.filename or "").suffix.lower()
    path = f"{notebook_id}/{doc_id}{ext}"
    supa.storage.from_("documents").upload(path, content, {"content-type": file.content_type or "application/octet-stream"})

    # 2. 插入 documents 行（status=parsing）
    supa.table("documents").insert({
        "id": doc_id,
        "notebook_id": notebook_id,
        "filename": file.filename,
        "storage_path": path,
        "mime": file.content_type,
        "status": "parsing",
    }).execute()

    # 3. 后台任务：解析 + 分块 + 嵌入
    background.add_task(_process_document, cfg, supa, doc_id, content, ext or ".txt")

    return {"document_id": doc_id, "status": "parsing"}


def _process_document(cfg, supa, doc_id: str, content: bytes, ext: str):
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        doc = parse(tmp_path)
        chunks = chunk(doc, target_tokens=800)

        eff = cfg.effective_embedding()
        if not eff["model"]:
            raise RuntimeError("embedding model 未配置")

        import asyncio
        texts = [c.content for c in chunks]
        vectors = asyncio.run(embed(
            texts=texts,
            provider=eff["provider"],
            api_key=eff["api_key"],
            base_url=eff["base_url"],
            model=eff["model"],
        ))

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

    except Exception as e:
        log.exception("文档解析失败 doc_id=%s", doc_id)
        supa.table("documents").update({"status": "failed"}).eq("id", doc_id).execute()


@router.get("/document/{doc_id}")
async def get_document(doc_id: str, request: Request):
    supa = request.app.state.supabase.client
    r = supa.table("documents").select("*").eq("id", doc_id).single().execute()
    if not r.data:
        raise HTTPException(404)
    return r.data
