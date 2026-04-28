import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import load_config
from routers import ai as ai_router
from services.ai.manager import AIProviderManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # state 在 create_app 中已初始化；lifespan 保留给未来扩展（如连接池）
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Noto", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    cfg = load_config()
    app.state.config = cfg
    app.state.ai_manager = AIProviderManager(cfg)

    @app.get("/api/health")
    def health():
        return {"ok": True}

    app.include_router(ai_router.router)
    return app


app = create_app()
