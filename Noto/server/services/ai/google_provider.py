"""Google Gemini Provider"""

from typing import AsyncIterator

from services.ai.base import AIProvider


class GoogleProvider(AIProvider):
    def __init__(self, api_key: str, base_url: str = "", model: str = ""):
        super().__init__(api_key, base_url, model)
        self.model = model or "gemini-2.5-flash"
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _convert(self, messages: list[dict]) -> list[dict]:
        out = []
        for m in messages:
            role = "user" if m["role"] == "user" else "model"
            out.append({"role": role, "parts": [{"text": m["content"]}]})
        return out

    async def chat(self, messages: list[dict], system: str = "") -> str:
        client = self._get_client()
        config = {"system_instruction": system} if system else None
        resp = await client.aio.models.generate_content(
            model=self.model,
            contents=self._convert(messages),
            config=config,
        )
        return resp.text or ""

    async def chat_stream(self, messages: list[dict], system: str = "") -> AsyncIterator[str]:
        client = self._get_client()
        config = {"system_instruction": system} if system else None
        async for chunk in await client.aio.models.generate_content_stream(
            model=self.model,
            contents=self._convert(messages),
            config=config,
        ):
            if chunk.text:
                yield chunk.text

    async def test_connection(self) -> dict:
        try:
            client = self._get_client()
            await client.aio.models.generate_content(
                model=self.model,
                contents="Hi",
            )
            return {"success": True, "message": f"连接成功 (模型: {self.model})"}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {e}"}
