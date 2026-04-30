"""学习对话：RAG + Socratic prompt + SSE"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from models.schemas import AskWithContextRequest, ChatSendRequest, CloseConversationRequest
from services.ai.embedding import embed
from services.ai.utils import SSE_DONE, SSE_HEADERS, extract_json, sse_event
from services.prompts import render_prompt
from services.retrieval import search

log = logging.getLogger("noto.chat")

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/send")
async def send(req: ChatSendRequest, request: Request):
    supa = request.app.state.supabase.client
    mgr = request.app.state.ai_manager
    cfg = request.app.state.config

    if not mgr.is_configured:
        raise HTTPException(400, "AI 未配置")

    conv_id = req.conversation_id
    if not conv_id:
        r = supa.table("conversations").insert({
            "notebook_id": req.notebook_id,
            "title": req.message[:30],
            "status": "active",
        }).execute()
        conv_id = r.data[0]["id"]

    nb = supa.table("notebooks").select("goal").eq("id", req.notebook_id).single().execute()
    goal = nb.data.get("goal", "") if nb.data else ""

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

    system = render_prompt("socratic", citations=citation_text, goal=goal or "（未设定）")

    hist = (
        supa.table("messages").select("role,content")
        .eq("conversation_id", conv_id)
        .order("created_at", desc=True).limit(10)
        .execute()
    )
    history = [{"role": m["role"], "content": m["content"]} for m in reversed(hist.data or [])]
    history.append({"role": "user", "content": req.message})

    supa.table("messages").insert({
        "conversation_id": conv_id,
        "role": "user",
        "content": req.message,
        "citations": None,
    }).execute()

    citations_payload = [{"chunk_id": c["id"], "page_num": c["page_num"]} for c in chunks]

    async def event_stream():
        full = ""
        try:
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


@router.post("/close-conversation")
async def close_conversation(req: CloseConversationRequest, request: Request):
    supa = request.app.state.supabase.client
    mgr = request.app.state.ai_manager

    conv = supa.table("conversations").select("notebook_id,status").eq("id", req.conversation_id).single().execute()
    if not conv.data:
        raise HTTPException(404, "对话不存在")
    if conv.data["status"] == "closed":
        return {"ok": True, "cards": []}

    msgs = supa.table("messages").select("role,content").eq("conversation_id", req.conversation_id).order("created_at").execute()
    transcript = "\n\n".join(f"{m['role']}: {m['content']}" for m in (msgs.data or []))

    prompt = render_prompt("card_extraction", transcript=transcript)
    raw = await mgr.chat([{"role": "user", "content": prompt}])
    parsed = extract_json(raw)
    if not isinstance(parsed, list):
        raise HTTPException(500, f"卡片提炼失败，原始回复：{raw[:200]}")

    rows = []
    for item in parsed:
        if not isinstance(item, dict) or "question" not in item or "answer" not in item:
            continue
        rows.append({
            "notebook_id": conv.data["notebook_id"],
            "source_conversation_id": req.conversation_id,
            "question": item["question"],
            "answer": item["answer"],
        })
    if rows:
        supa.table("cards").insert(rows).execute()

    supa.table("conversations").update({
        "status": "closed",
        "closed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", req.conversation_id).execute()

    return {"ok": True, "cards": rows}


@router.post("/ask-with-context")
async def ask_with_context(req: AskWithContextRequest, request: Request):
    """
    User selected text in a document and asks AI about it.
    Creates a skeleton_node of type `user_selection` + card, then streams AI response.
    """
    supa = request.app.state.supabase.client
    mgr = request.app.state.ai_manager
    if not mgr.is_configured:
        raise HTTPException(400, "AI 未配置")

    # Ensure skeleton exists (user_selection nodes still attach to the space skeleton)
    sk = supa.table("skeletons").select("id").eq("notebook_id", str(req.notebook_id)).maybe_single().execute()
    if not sk.data:
        sk_new = supa.table("skeletons").insert({"notebook_id": str(req.notebook_id), "status": "ready"}).execute()
        skeleton_id = sk_new.data[0]["id"]
    else:
        skeleton_id = sk.data["id"]

    # Node type maps from action
    node_type_map = {"ask": "question", "mark_stuck": "question", "save_note": "claim"}
    initial_state_map = {"ask": "thinking", "mark_stuck": "stuck", "save_note": "thinking"}

    node_id = str(uuid.uuid4())
    supa.table("skeleton_nodes").insert({
        "id": node_id,
        "skeleton_id": skeleton_id,
        "notebook_id": str(req.notebook_id),
        "node_type": node_type_map.get(req.action, "question"),
        "title": req.user_question or req.selected_text[:50],
        "body": req.selected_text,
        "source_positions": [{"document_id": str(req.document_id), "chunk_id": str(req.chunk_id) if req.chunk_id else None}],
        "card_source": "user_selection",
    }).execute()

    # Create matching card in initial state
    card_r = supa.table("cards").insert({
        "notebook_id": str(req.notebook_id),
        "skeleton_node_id": node_id,
        "question": req.user_question or req.selected_text[:50],
        "answer": "",
        "card_state": initial_state_map.get(req.action, "thinking"),
    }).execute()

    return {
        "node_id": node_id,
        "card_id": card_r.data[0]["id"] if card_r.data else None,
    }
