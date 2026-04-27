"""三层配置：默认值 → .env → data/config.json"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


@dataclass
class Config:
    project_root: Path = field(default_factory=_project_root)
    data_dir: str = ""

    ai_provider: str = ""
    ai_api_key: str = ""
    ai_base_url: str = ""
    ai_model: str = ""

    embedding_provider: str = ""
    embedding_api_key: str = ""
    embedding_base_url: str = ""
    embedding_model: str = ""

    supabase_url: str = ""
    supabase_service_key: str = ""

    def __post_init__(self):
        if not self.data_dir:
            self.data_dir = str(self.project_root / "server" / "data")

    @property
    def config_json_path(self) -> str:
        return str(Path(self.data_dir) / "config.json")

    def get_safe_settings(self) -> dict:
        return {
            "ai_provider": self.ai_provider,
            "ai_base_url": self.ai_base_url,
            "ai_model": self.ai_model,
            "ai_api_key_set": bool(self.ai_api_key),
            "embedding_provider": self.embedding_provider,
            "embedding_base_url": self.embedding_base_url,
            "embedding_model": self.embedding_model,
            "embedding_api_key_set": bool(self.embedding_api_key),
            "supabase_url": self.supabase_url,
            "supabase_service_key_set": bool(self.supabase_service_key),
        }

    def effective_embedding(self) -> dict:
        """返回 embedding 的有效配置，空字段 fallback 到 ai_*。model 必须非空。"""
        return {
            "provider": self.embedding_provider or self.ai_provider,
            "api_key": self.embedding_api_key or self.ai_api_key,
            "base_url": self.embedding_base_url or self.ai_base_url,
            "model": self.embedding_model,
        }


def load_config() -> Config:
    root = _project_root()
    cfg = Config(
        project_root=root,
        data_dir=os.environ.get("NOTO_DATA_DIR", str(root / "server" / "data")),
        ai_provider=os.environ.get("NOTO_AI_PROVIDER", ""),
        ai_api_key=os.environ.get("NOTO_AI_API_KEY", ""),
        ai_base_url=os.environ.get("NOTO_AI_BASE_URL", ""),
        ai_model=os.environ.get("NOTO_AI_MODEL", ""),
        embedding_provider=os.environ.get("NOTO_EMBEDDING_PROVIDER", ""),
        embedding_api_key=os.environ.get("NOTO_EMBEDDING_API_KEY", ""),
        embedding_base_url=os.environ.get("NOTO_EMBEDDING_BASE_URL", ""),
        embedding_model=os.environ.get("NOTO_EMBEDDING_MODEL", ""),
        supabase_url=os.environ.get("NOTO_SUPABASE_URL", ""),
        supabase_service_key=os.environ.get("NOTO_SUPABASE_SERVICE_KEY", ""),
    )

    cfg_file = Path(cfg.data_dir) / "config.json"
    if cfg_file.exists():
        try:
            user = json.loads(cfg_file.read_text(encoding="utf-8"))
            for key in [
                "ai_provider", "ai_api_key", "ai_base_url", "ai_model",
                "embedding_provider", "embedding_api_key",
                "embedding_base_url", "embedding_model",
                "supabase_url", "supabase_service_key",
            ]:
                v = user.get(key)
                if v:
                    setattr(cfg, key, v)
        except (json.JSONDecodeError, OSError):
            pass

    return cfg


def save_user_config(cfg: Config, updates: dict):
    path = Path(cfg.config_json_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    existing = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    for k, v in updates.items():
        if v is not None:
            existing[k] = v
            setattr(cfg, k, v)

    path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
