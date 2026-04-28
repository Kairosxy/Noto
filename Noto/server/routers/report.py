"""阶段评估报告"""

import json

from fastapi import APIRouter, HTTPException, Request

from models.schemas import ReportGenerateRequest
from services.prompts import render_prompt

router = APIRouter(prefix="/api/report", tags=["report"])


@router.post("/generate")
async def generate(req: ReportGenerateRequest, request: Request):
    supa = request.app.state.supabase.client
    mgr = request.app.state.ai_manager
    if not mgr.is_configured:
        raise HTTPException(400, "AI 未配置")

    from_iso = f"{req.from_date.isoformat()}T00:00:00Z"
    to_iso = f"{req.to_date.isoformat()}T23:59:59Z"

    convs = supa.table("conversations").select("id,title,started_at").eq("notebook_id", req.notebook_id).gte("started_at", from_iso).lte("started_at", to_iso).execute()
    conv_list = convs.data or []
    conv_ids = [c["id"] for c in conv_list]

    by_conv: dict[str, list[dict]] = {}
    if conv_ids:
        msgs = supa.table("messages").select("conversation_id,role,content").in_("conversation_id", conv_ids).order("created_at").execute()
        for m in msgs.data or []:
            by_conv.setdefault(m["conversation_id"], []).append(m)

    conv_summaries = [
        {
            "title": c["title"],
            "messages": [{"role": m["role"], "content": m["content"][:80]} for m in by_conv.get(c["id"], [])[:10]],
        }
        for c in conv_list
    ]

    cards = supa.table("cards").select("question,answer,ease,reps").eq("notebook_id", req.notebook_id).order("created_at", desc=True).limit(20).execute()

    reviews = supa.table("reviews").select("rating,reviewed_at,card_id").gte("reviewed_at", from_iso).lte("reviewed_at", to_iso).execute()
    stats = {"total": 0, "again": 0, "hard": 0, "good": 0, "easy": 0}
    for r in reviews.data or []:
        stats["total"] += 1
        stats[r["rating"]] = stats.get(r["rating"], 0) + 1

    data_payload = json.dumps({
        "conversations": conv_summaries,
        "review_stats": stats,
        "top_cards": cards.data or [],
    }, ensure_ascii=False, indent=2)

    prompt = render_prompt(
        "report",
        from_date=req.from_date.isoformat(),
        to_date=req.to_date.isoformat(),
        data=data_payload,
    )

    markdown = await mgr.chat([{"role": "user", "content": prompt}])

    r = supa.table("reports").insert({
        "notebook_id": req.notebook_id,
        "from_date": req.from_date.isoformat(),
        "to_date": req.to_date.isoformat(),
        "content": markdown,
    }).execute()

    return r.data[0]


@router.get("")
async def list_reports(notebook_id: str, request: Request):
    supa = request.app.state.supabase.client
    r = supa.table("reports").select("*").eq("notebook_id", notebook_id).order("generated_at", desc=True).execute()
    return r.data or []
