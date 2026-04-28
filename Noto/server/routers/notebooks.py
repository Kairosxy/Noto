"""Notebook CRUD"""

from fastapi import APIRouter, HTTPException, Request

from models.schemas import NotebookCreate

router = APIRouter(prefix="/api/notebooks", tags=["notebooks"])


@router.post("")
async def create_notebook(req: NotebookCreate, request: Request):
    supa = request.app.state.supabase.client
    r = supa.table("notebooks").insert({
        "title": req.title,
        "goal": req.goal,
    }).execute()
    return r.data[0]


@router.get("")
async def list_notebooks(request: Request):
    supa = request.app.state.supabase.client
    r = supa.table("notebooks").select("*").order("created_at", desc=True).execute()
    return r.data


@router.get("/{notebook_id}")
async def get_notebook(notebook_id: str, request: Request):
    supa = request.app.state.supabase.client
    r = supa.table("notebooks").select("*").eq("id", notebook_id).single().execute()
    if not r.data:
        raise HTTPException(404)
    return r.data


@router.get("/{notebook_id}/documents")
async def list_documents(notebook_id: str, request: Request):
    supa = request.app.state.supabase.client
    r = supa.table("documents").select("*").eq("notebook_id", notebook_id).order("created_at", desc=True).execute()
    return r.data
