"""AI 路由：测连接 / 聊天 / 配置"""

import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from models.schemas import AIChatRequest, SettingsUpdateRequest, TestConnectionRequest
from services.ai.manager import AIProviderManager
from services.ai.utils import SSE_DONE, SSE_HEADERS, sse_event

log = logging.getLogger("noto.ai.router")

router = APIRouter(prefix="/api", tags=["ai"])


def _mgr(request: Request) -> AIProviderManager:
    return request.app.state.ai_manager


@router.post("/ai/test-connection")
async def test_connection(req: TestConnectionRequest, request: Request):
    api_key = req.api_key
    if api_key == "__use_saved__":
        api_key = request.app.state.config.ai_api_key
    if not api_key:
        raise HTTPException(400, "未提供 API Key")
    result = await AIProviderManager.test_with_params(
        provider=req.provider,
        api_key=api_key,
        base_url=req.base_url,
        model=req.model,
    )
    if not result["success"]:
        raise HTTPException(400, result["message"])
    return result


@router.post("/ai/chat")
async def chat_stream(req: AIChatRequest, request: Request):
    mgr = _mgr(request)
    if not mgr.is_configured:
        raise HTTPException(400, "AI 未配置")
    messages = [m.model_dump() for m in req.messages]

    async def event_stream():
        try:
            async for chunk in mgr.chat_stream(messages, req.system):
                yield sse_event({"content": chunk})
            yield SSE_DONE
        except Exception as e:
            yield sse_event({"error": str(e)})
            yield SSE_DONE

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=SSE_HEADERS)


@router.get("/settings")
async def get_settings(request: Request):
    return request.app.state.config.get_safe_settings()


@router.post("/settings")
async def update_settings(req: SettingsUpdateRequest, request: Request):
    from config import save_user_config, load_config
    cfg = request.app.state.config
    updates = req.model_dump(exclude_none=True)
    save_user_config(cfg, updates)
    # 重新加载配置并刷新 manager
    new_cfg = load_config()
    request.app.state.config = new_cfg
    request.app.state.ai_manager.refresh(new_cfg)
    request.app.state.supabase.refresh(new_cfg)
    return new_cfg.get_safe_settings()
