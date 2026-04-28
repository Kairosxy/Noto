"""supabase-py 客户端单例（service role）"""

from supabase import Client, create_client

from config import Config


class SupabaseClient:
    def __init__(self, cfg: Config):
        self._client: Client | None = None
        self._cfg = cfg

    @property
    def client(self) -> Client:
        if self._client is None:
            if not self._cfg.supabase_url or not self._cfg.supabase_service_key:
                raise RuntimeError("Supabase 未配置")
            self._client = create_client(self._cfg.supabase_url, self._cfg.supabase_service_key)
        return self._client

    def refresh(self, cfg: Config):
        self._cfg = cfg
        self._client = None
