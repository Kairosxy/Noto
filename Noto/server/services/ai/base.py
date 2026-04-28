"""AI Provider 抽象"""

from abc import ABC, abstractmethod
from typing import AsyncIterator


class AIProvider(ABC):
    def __init__(self, api_key: str, base_url: str = "", model: str = ""):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    @abstractmethod
    async def chat(self, messages: list[dict], system: str = "") -> str: ...

    @abstractmethod
    async def chat_stream(self, messages: list[dict], system: str = "") -> AsyncIterator[str]: ...

    @abstractmethod
    async def _ping(self) -> str:
        """发一个最小请求，返回服务端报告的模型名（或 self.model 作为回退）。"""
        ...

    async def test_connection(self) -> dict:
        try:
            used = await self._ping()
            return {"success": True, "message": f"连接成功 (模型: {used})"}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {e}"}
