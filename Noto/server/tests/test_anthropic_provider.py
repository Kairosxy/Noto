from unittest.mock import AsyncMock, MagicMock

import pytest

from services.ai.anthropic_provider import AnthropicProvider


@pytest.fixture
def mock_anthropic(monkeypatch):
    client = MagicMock()
    client.messages.create = AsyncMock()
    monkeypatch.setattr(
        "services.ai.anthropic_provider.AnthropicProvider._get_client",
        lambda self: client,
    )
    return client


async def test_chat_returns_first_block_text(mock_anthropic):
    mock_anthropic.messages.create.return_value = MagicMock(
        content=[MagicMock(text="hi")]
    )
    p = AnthropicProvider(api_key="k", model="claude-sonnet-4")
    result = await p.chat([{"role": "user", "content": "hi"}])
    assert result == "hi"


async def test_chat_passes_system_as_toplevel(mock_anthropic):
    mock_anthropic.messages.create.return_value = MagicMock(content=[MagicMock(text="ok")])
    p = AnthropicProvider(api_key="k", model="claude-sonnet-4")
    await p.chat([{"role": "user", "content": "hi"}], system="you are X")
    args = mock_anthropic.messages.create.call_args.kwargs
    assert args["system"] == "you are X"
    assert args["messages"] == [{"role": "user", "content": "hi"}]
