"""学习对话：RAG + Socratic prompt + SSE"""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from models.schemas import ChatSendRequest
from services.ai.embedding import embed
from services.ai.utils import SSE_DONE, SSE_HEADERS, sse_event
from services.retrieval import search

log = logging.getLogger("noto.chat")

router = APIRouter(prefix="/api/chat", tags=["chat"])

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "socratic.md"


def _load_socratic_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


@router.post("/send")
async def send(req: ChatSendRequest, request: Request):
    supa = request.app.state.supabase.client
    mgr = request.app.state.ai_manager
    cfg = request.app.state.config

    if not mgr.is_configured:
        raise HTTPException(400, "AI 未配置")

    # 1. 获取或创建 conversation
    conv_id = req.conversation_id
    if not conv_id:
        r = supa.table("conversations").insert({
            "notebook_id": req.notebook_id,
            "title": req.message[:30],
            "status": "active",
        }).execute()
        conv_id = r.data[0]["id"]

    # 2. 载入 notebook 信息（拿 goal）
    nb = supa.table("notebooks").select("goal").eq("id", req.notebook_id).single().execute()
    goal = nb.data.get("goal", "") if nb.data else ""

    # 3. 检索相关 chunks
    eff = cfg.effective_embedding()
    query_vecs = await embed(
        texts=[req.message],
        provider=eff["provider"],
        api_key=eff["api_key"],
        base_url=eff["base_url"],
        model=eff["model"],
    )
    chunks = search(supa, notebook_id=req.notebook_id, query_embedding=query_vecs[0], k=5)

    citation_text = "\n\n".join(
        f"[片段 {i+1}, p.{c['page_num']}]\n{c['content']}" for i, c in enumerate(chunks)
    ) or "（暂无资料，只能走开放式引导）"

    system = _load_socratic_prompt().replace("{citations}", citation_text).replace("{goal}", goal or "（未设定）")

    # 4. 载入历史（最近 10 条）
    hist = supa.table("messages").select("role,content").eq("conversation_id", conv_id).order("created_at").execute()
    history = [{"role": m["role"], "content": m["content"]} for m in (hist.data or [])[-10:]]
    history.append({"role": "user", "content": req.message})

    # 5. 插入用户消息
    supa.table("messages").insert({
        "conversation_id": conv_id,
        "role": "user",
        "content": req.message,
        "citations": None,
    }).execute()

    # 6. 流式返回 + 结束时写入 assistant 消息
    citations_payload = [{"chunk_id": c["id"], "page_num": c["page_num"]} for c in chunks]

    async def event_stream():
        full = ""
        try:
            # 首帧先把 conv_id + citations 发给前端
            yield sse_event({"conversation_id": conv_id, "citations": citations_payload})
            async for chunk_text in mgr.chat_stream(history, system):
                full += chunk_text
                yield sse_event({"content": chunk_text})
            supa.table("messages").insert({
                "conversation_id": conv_id,
                "role": "assistant",
                "content": full,
                "citations": citations_payload,
            }).execute()
            yield SSE_DONE
        except Exception as e:
            yield sse_event({"error": str(e)})
            yield SSE_DONE

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=SSE_HEADERS)


@router.get("/messages")
async def list_messages(conversation_id: str, request: Request):
    supa = request.app.state.supabase.client
    r = supa.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at").execute()
    return r.data or []


@router.get("/conversations")
async def list_conversations(notebook_id: str, request: Request):
    supa = request.app.state.supabase.client
    r = supa.table("conversations").select("*").eq("notebook_id", notebook_id).order("started_at", desc=True).execute()
    return r.data or []
