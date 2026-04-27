"""OpenAI 兼容 Provider（覆盖 GPT / DeepSeek / Qwen / Ollama 等 OpenAI-API-兼容的服务）"""

from typing import AsyncIterator

from services.ai.base import AIProvider


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, base_url: str = "", model: str = ""):
        super().__init__(api_key, base_url, model)
        self.model = model or "gpt-4o"
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = AsyncOpenAI(**kwargs)
        return self._client

    def _build_messages(self, messages: list[dict], system: str) -> list[dict]:
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend(messages)
        return msgs

    async def chat(self, messages: list[dict], system: str = "") -> str:
        client = self._get_client()
        resp = await client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(messages, system),
        )
        return resp.choices[0].message.content or ""

    async def chat_stream(self, messages: list[dict], system: str = "") -> AsyncIterator[str]:
        client = self._get_client()
        stream = await client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(messages, system),
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    async def test_connection(self) -> dict:
        try:
            client = self._get_client()
            resp = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
            )
            used = resp.model or self.model
            return {"success": True, "message": f"连接成功 (模型: {used})"}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {e}"}
