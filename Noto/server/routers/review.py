"""复习：拿到期卡 / 评分"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from models.schemas import RateRequest
from services.sm2 import next_due

router = APIRouter(prefix="/api/review", tags=["review"])


@router.get("/due")
async def due(notebook_id: str, request: Request, limit: int = 20):
    supa = request.app.state.supabase.client
    now_iso = datetime.now(timezone.utc).isoformat()
    r = supa.table("cards").select("*").eq("notebook_id", notebook_id).lte("due_at", now_iso).order("due_at").limit(limit).execute()
    return r.data or []


@router.post("/rate")
async def rate(req: RateRequest, request: Request):
    supa = request.app.state.supabase.client
    card = supa.table("cards").select("ease,reps").eq("id", req.card_id).single().execute()
    if not card.data:
        raise HTTPException(404)

    new_due, new_ease, new_reps = next_due(
        rating=req.rating,
        ease=card.data["ease"],
        reps=card.data["reps"],
    )

    supa.table("cards").update({
        "due_at": new_due.isoformat(),
        "ease": new_ease,
        "reps": new_reps,
    }).eq("id", req.card_id).execute()

    supa.table("reviews").insert({
        "card_id": req.card_id,
        "rating": req.rating,
    }).execute()

    return {
        "due_at": new_due.isoformat(),
        "ease": new_ease,
        "reps": new_reps,
    }
