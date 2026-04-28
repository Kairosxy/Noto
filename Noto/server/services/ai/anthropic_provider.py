"""Anthropic Claude Provider"""

from typing import AsyncIterator

from services.ai.base import AIProvider


class AnthropicProvider(AIProvider):
    def __init__(self, api_key: str, base_url: str = "", model: str = ""):
        super().__init__(api_key, base_url, model)
        self.model = model or "claude-sonnet-4-5"
        self._client = None

    def _get_client(self):
        if self._client is None:
            from anthropic import AsyncAnthropic
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = AsyncAnthropic(**kwargs)
        return self._client

    async def chat(self, messages: list[dict], system: str = "") -> str:
        client = self._get_client()
        kwargs = {"model": self.model, "max_tokens": 4096, "messages": messages}
        if system:
            kwargs["system"] = system
        resp = await client.messages.create(**kwargs)
        return resp.content[0].text if resp.content else ""

    async def chat_stream(self, messages: list[dict], system: str = "") -> AsyncIterator[str]:
        client = self._get_client()
        kwargs = {"model": self.model, "max_tokens": 4096, "messages": messages}
        if system:
            kwargs["system"] = system
        async with client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    async def _ping(self) -> str:
        resp = await self._get_client().messages.create(
            model=self.model,
            max_tokens=5,
            messages=[{"role": "user", "content": "Hi"}],
        )
        return resp.model or self.model
