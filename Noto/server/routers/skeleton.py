"""Skeleton 路由：空间级骨架 CRUD + 重新蒸馏。"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from models.schemas import MergeNodeRequest, RejectNodeRequest
from services.distill import distill_space_skeleton

log = logging.getLogger("noto.skeleton")

router = APIRouter(prefix="/api/notebooks", tags=["skeleton"])


@router.get("/{notebook_id}/skeleton")
async def get_skeleton(notebook_id: str, request: Request):
    supa = request.app.state.supabase.client

    sk = supa.table("skeletons").select("*").eq("notebook_id", notebook_id).maybe_single().execute()
    if sk is None or not sk.data:
        return {"id": None, "status": "not_generated"}

    skeleton_id = sk.data["id"]
    dirs = supa.table("learning_directions").select("*").eq("skeleton_id", skeleton_id).order("position").execute()
    nodes = supa.table("skeleton_nodes").select("*").eq("skeleton_id", skeleton_id).is_("rejected_at", None).execute()
    assocs = supa.table("skeleton_node_directions").select("*").execute()

    # Fold node_ids into each direction
    node_ids_by_dir: dict[str, list[str]] = {}
    for a in assocs.data or []:
        node_ids_by_dir.setdefault(a["direction_id"], []).append(a["node_id"])

    dirs_out = [{**d, "node_ids": node_ids_by_dir.get(d["id"], [])} for d in (dirs.data or [])]

    return {
        **sk.data,
        "directions": dirs_out,
        "nodes": nodes.data or [],
    }


@router.post("/{notebook_id}/skeleton/regenerate")
async def regenerate_skeleton(notebook_id: str, request: Request, background: BackgroundTasks):
    supa = request.app.state.supabase.client
    mgr = request.app.state.ai_manager
    if not mgr.is_configured:
        raise HTTPException(400, "AI 未配置")

    nb = supa.table("notebooks").select("goal").eq("id", notebook_id).single().execute()
    goal = nb.data.get("goal", "") if nb.data else ""

    docs = supa.table("documents").select("id,filename,summary").eq("notebook_id", notebook_id).eq("status", "ready").execute()
    docs_summaries = [
        {"document_id": d["id"], "title": d["filename"], "summary": d.get("summary") or ""}
        for d in (docs.data or [])
        if d.get("summary")
    ]
    if not docs_summaries:
        raise HTTPException(400, "空间内还没有蒸馏完成的文档")

    # Upsert skeleton row as 'generating'
    existing = supa.table("skeletons").select("id").eq("notebook_id", notebook_id).maybe_single().execute()
    if existing is not None and existing.data:
        skeleton_id = existing.data["id"]
        supa.table("skeletons").update({"status": "generating"}).eq("id", skeleton_id).execute()
    else:
        r = supa.table("skeletons").insert({"notebook_id": notebook_id, "status": "generating"}).execute()
        skeleton_id = r.data[0]["id"]

    background.add_task(_run_skeleton_distill, mgr, supa, skeleton_id, notebook_id, goal, docs_summaries)
    return {"skeleton_id": skeleton_id, "status": "generating"}


def _run_skeleton_distill(mgr, supa, skeleton_id: str, notebook_id: str, goal: str, docs_summaries: list[dict]):
    try:
        result = asyncio.run(distill_space_skeleton(mgr, goal, docs_summaries))

        # Clear old nodes/directions/assocs for this skeleton
        old_dirs = supa.table("learning_directions").select("id").eq("skeleton_id", skeleton_id).execute().data or []
        old_dir_ids = [d["id"] for d in old_dirs]
        if old_dir_ids:
            supa.table("skeleton_node_directions").delete().in_("direction_id", old_dir_ids).execute()
        supa.table("learning_directions").delete().eq("skeleton_id", skeleton_id).execute()
        supa.table("skeleton_nodes").delete().eq("skeleton_id", skeleton_id).execute()

        # Insert new nodes, collect temp_id -> real_id
        temp_to_real: dict[str, str] = {}
        for n in result["nodes"]:
            real_id = str(uuid.uuid4())
            temp_to_real[n["temp_id"]] = real_id
            supa.table("skeleton_nodes").insert({
                "id": real_id,
                "skeleton_id": skeleton_id,
                "notebook_id": notebook_id,
                "node_type": n["node_type"],
                "title": n["title"],
                "body": n.get("body"),
                "source_positions": n.get("source_positions"),
                "card_source": "ai_generated",
            }).execute()

        # Insert directions and associate nodes
        for d in result["directions"]:
            dir_r = supa.table("learning_directions").insert({
                "skeleton_id": skeleton_id,
                "notebook_id": notebook_id,
                "position": d["position"],
                "title": d["title"],
                "description": d.get("description"),
                "estimated_minutes": d.get("estimated_minutes"),
            }).execute()
            direction_id = dir_r.data[0]["id"]
            for temp_id in d.get("node_ids", []):
                real_id = temp_to_real.get(temp_id)
                if real_id:
                    supa.table("skeleton_node_directions").insert({
                        "direction_id": direction_id,
                        "node_id": real_id,
                    }).execute()

        supa.table("skeletons").update({
            "space_summary": result.get("space_summary"),
            "status": "ready",
        }).eq("id", skeleton_id).execute()

    except Exception as e:
        log.exception("skeleton distill failed")
        supa.table("skeletons").update({"status": "failed"}).eq("id", skeleton_id).execute()


@router.post("/{notebook_id}/documents/backfill-summaries")
async def backfill_summaries(notebook_id: str, request: Request, background: BackgroundTasks):
    """For v1 notebooks: trigger summary generation for all documents that lack one."""
    supa = request.app.state.supabase.client
    mgr = request.app.state.ai_manager
    if not mgr.is_configured:
        raise HTTPException(400, "AI 未配置")

    docs = supa.table("documents").select("id").eq("notebook_id", notebook_id).eq("status", "ready").is_("summary", None).execute()
    count = len(docs.data or [])
    if count == 0:
        return {"count": 0, "status": "nothing_to_do"}

    def _backfill():
        from services.distill import distill_doc_summary
        import asyncio as aio
        for d in (docs.data or []):
            chunks = supa.table("chunks").select("content").eq("document_id", d["id"]).order("position").execute()
            if not chunks.data:
                continue
            full_text = "\n\n".join(c["content"] for c in chunks.data)[:60000]
            try:
                summary = aio.run(distill_doc_summary(mgr, full_text))
                supa.table("documents").update({"summary": summary}).eq("id", d["id"]).execute()
            except Exception as e:
                log.warning("backfill failed for %s: %s", d["id"], e)

    background.add_task(_backfill)
    return {"count": count, "status": "started"}


node_router = APIRouter(prefix="/api/skeleton-nodes", tags=["skeleton-nodes"])


@node_router.post("/{node_id}/reject")
async def reject_node(node_id: str, req: RejectNodeRequest, request: Request):
    supa = request.app.state.supabase.client
    supa.table("skeleton_nodes").update({
        "rejected_at": datetime.now(timezone.utc).isoformat(),
        "rejected_reason": req.reason,
    }).eq("id", node_id).execute()
    return {"ok": True}


@node_router.post("/{node_id}/merge-into")
async def merge_node(node_id: str, req: MergeNodeRequest, request: Request):
    supa = request.app.state.supabase.client
    supa.table("skeleton_nodes").update({
        "merged_into": str(req.target_node_id),
    }).eq("id", node_id).execute()
    return {"ok": True}
