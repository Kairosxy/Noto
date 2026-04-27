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
    async def test_connection(self) -> dict:
        """{success: bool, message: str}"""
        ...
