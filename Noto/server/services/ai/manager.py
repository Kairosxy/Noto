"""AI Provider 工厂"""

import importlib
import logging

from services.ai.base import AIProvider

log = logging.getLogger("noto.ai")


class AIProviderManager:
    PROVIDERS = {
        "openai": "services.ai.openai_provider.OpenAIProvider",
        "anthropic": "services.ai.anthropic_provider.AnthropicProvider",
        "google": "services.ai.google_provider.GoogleProvider",
    }

    def __init__(self, config):
        self._config = config
        self._provider: AIProvider | None = None
        self._build()

    def _build(self):
        if not self._config.ai_provider or not self._config.ai_api_key:
            self._provider = None
            return
        cls_path = self.PROVIDERS.get(self._config.ai_provider)
        if not cls_path:
            self._provider = None
            return
        module_path, cls_name = cls_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        cls = getattr(module, cls_name)
        self._provider = cls(
            api_key=self._config.ai_api_key,
            base_url=self._config.ai_base_url,
            model=self._config.ai_model,
        )

    def refresh(self, config):
        self._config = config
        self._build()

    @property
    def provider(self) -> AIProvider | None:
        return self._provider

    @property
    def is_configured(self) -> bool:
        return self._provider is not None

    async def chat(self, messages: list[dict], system: str = "") -> str:
        if not self._provider:
            raise RuntimeError("AI 未配置")
        return await self._provider.chat(messages, system)

    async def chat_stream(self, messages: list[dict], system: str = ""):
        if not self._provider:
            raise RuntimeError("AI 未配置")
        async for chunk in self._provider.chat_stream(messages, system):
            yield chunk

    async def test_connection(self) -> dict:
        if not self._provider:
            return {"success": False, "message": "AI 未配置"}
        return await self._provider.test_connection()

    @classmethod
    async def test_with_params(cls, provider: str, api_key: str, base_url: str = "", model: str = "") -> dict:
        cls_path = cls.PROVIDERS.get(provider)
        if not cls_path:
            return {"success": False, "message": f"不支持的提供商: {provider}"}
        module_path, cls_name = cls_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        provider_cls = getattr(module, cls_name)
        return await provider_cls(api_key=api_key, base_url=base_url, model=model).test_connection()
