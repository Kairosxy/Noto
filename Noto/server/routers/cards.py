"""Card 状态 + 评判路由"""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Request

from models.schemas import CardStateUpdate, EvaluateExplanationRequest, EvaluateExplanationResponse
from services.evaluate import evaluate_explanation

router = APIRouter(prefix="/api/cards", tags=["cards"])


@router.patch("/{card_id}/state")
async def update_state(card_id: str, req: CardStateUpdate, request: Request):
    supa = request.app.state.supabase.client

    updates: dict = {"card_state": req.state}
    if req.user_explanation is not None:
        updates["user_explanation"] = req.user_explanation

    # Transitioning to got_it with explanation → init SM-2
    if req.state == "got_it":
        if not req.user_explanation or not req.user_explanation.strip():
            raise HTTPException(400, "got_it 必须提供 user_explanation")
        updates["due_at"] = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        updates.setdefault("ease", 0)
        updates.setdefault("reps", 0)

    r = supa.table("cards").update(updates).eq("id", card_id).execute()
    if not r.data:
        raise HTTPException(404, "card 不存在")
    return r.data[0]


@router.post("/{card_id}/evaluate", response_model=EvaluateExplanationResponse)
async def evaluate(card_id: str, req: EvaluateExplanationRequest, request: Request):
    if str(req.card_id) != card_id:
        raise HTTPException(400, "card_id 不一致")

    supa = request.app.state.supabase.client
    mgr = request.app.state.ai_manager
    if not mgr.is_configured:
        raise HTTPException(400, "AI 未配置")

    # Join card -> skeleton_node to get context
    card = supa.table("cards").select("skeleton_node_id").eq("id", card_id).single().execute()
    if not card.data:
        raise HTTPException(404, "card 不存在")

    node_title = ""
    node_body = ""
    citations = ""

    node_id = card.data.get("skeleton_node_id")
    if node_id:
        node = supa.table("skeleton_nodes").select("title,body,source_positions").eq("id", node_id).single().execute()
        if node.data:
            node_title = node.data["title"]
            node_body = node.data.get("body") or ""
            positions = node.data.get("source_positions") or []
            if positions:
                chunk_ids = [p.get("chunk_id") for p in positions if p.get("chunk_id")]
                if chunk_ids:
                    cks = supa.table("chunks").select("id,content,page_num").in_("id", chunk_ids).execute()
                    citations = "\n\n".join(f"[p.{c.get('page_num')}] {c['content']}" for c in (cks.data or []))

    result = await evaluate_explanation(
        manager=mgr,
        node_title=node_title,
        node_body=node_body,
        citations=citations,
        user_explanation=req.user_explanation,
    )
    return result


@router.get("")
async def list_cards(notebook_id: str, request: Request, state: str | None = None):
    supa = request.app.state.supabase.client
    q = supa.table("cards").select("*").eq("notebook_id", notebook_id).order("due_at", desc=True)
    if state:
        q = q.eq("card_state", state)
    return q.execute().data or []
