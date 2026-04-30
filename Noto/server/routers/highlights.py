"""Highlights: persistent selection marks on original text."""

from fastapi import APIRouter, HTTPException, Request

from models.schemas import HighlightCreate

router = APIRouter(prefix="/api/highlights", tags=["highlights"])


@router.post("")
async def create_highlight(req: HighlightCreate, request: Request):
    supa = request.app.state.supabase.client
    # lookup notebook_id from document
    doc = supa.table("documents").select("notebook_id").eq("id", str(req.document_id)).single().execute()
    if not doc.data:
        raise HTTPException(404, "文档不存在")

    r = supa.table("highlights").insert({
        "document_id": str(req.document_id),
        "chunk_id": str(req.chunk_id) if req.chunk_id else None,
        "text": req.text,
        "notebook_id": doc.data["notebook_id"],
    }).execute()
    return r.data[0]


@router.get("")
async def list_highlights(document_id: str, request: Request):
    supa = request.app.state.supabase.client
    r = supa.table("highlights").select("*").eq("document_id", document_id).order("created_at").execute()
    return r.data or []


@router.delete("/{highlight_id}")
async def delete_highlight(highlight_id: str, request: Request):
    supa = request.app.state.supabase.client
    supa.table("highlights").delete().eq("id", highlight_id).execute()
    return {"ok": True}
