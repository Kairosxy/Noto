import pytest

from config import Config
from services.ai.manager import AIProviderManager
from services.ai.openai_provider import OpenAIProvider
from services.ai.anthropic_provider import AnthropicProvider


def test_unconfigured_manager_has_no_provider():
    cfg = Config()
    mgr = AIProviderManager(cfg)
    assert mgr.provider is None
    assert mgr.is_configured is False


def test_openai_configured():
    cfg = Config(ai_provider="openai", ai_api_key="k", ai_model="gpt-4o")
    mgr = AIProviderManager(cfg)
    assert isinstance(mgr.provider, OpenAIProvider)
    assert mgr.is_configured


def test_anthropic_configured():
    cfg = Config(ai_provider="anthropic", ai_api_key="k", ai_model="claude-sonnet-4-5")
    mgr = AIProviderManager(cfg)
    assert isinstance(mgr.provider, AnthropicProvider)


def test_unknown_provider_is_noop():
    cfg = Config(ai_provider="wat", ai_api_key="k")
    mgr = AIProviderManager(cfg)
    assert mgr.provider is None


def test_refresh_rebuilds_provider():
    cfg = Config()
    mgr = AIProviderManager(cfg)
    cfg.ai_provider = "openai"
    cfg.ai_api_key = "k"
    cfg.ai_model = "gpt-4o"
    mgr.refresh(cfg)
    assert isinstance(mgr.provider, OpenAIProvider)


async def test_chat_raises_when_unconfigured():
    cfg = Config()
    mgr = AIProviderManager(cfg)
    with pytest.raises(RuntimeError):
        await mgr.chat([{"role": "user", "content": "hi"}])
