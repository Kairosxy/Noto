from unittest.mock import AsyncMock, MagicMock

import pytest

from services.ai.openai_provider import OpenAIProvider


@pytest.fixture
def mock_openai(monkeypatch):
    fake_client = MagicMock()
    fake_client.chat.completions.create = AsyncMock()
    monkeypatch.setattr(
        "services.ai.openai_provider.OpenAIProvider._get_client",
        lambda self: fake_client,
    )
    return fake_client


async def test_chat_returns_text(mock_openai):
    mock_openai.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="hello"))]
    )
    p = OpenAIProvider(api_key="k", model="gpt-4o")
    result = await p.chat([{"role": "user", "content": "hi"}])
    assert result == "hello"


async def test_chat_prepends_system(mock_openai):
    mock_openai.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="ok"))]
    )
    p = OpenAIProvider(api_key="k", model="gpt-4o")
    await p.chat([{"role": "user", "content": "hi"}], system="you are X")
    args = mock_openai.chat.completions.create.call_args.kwargs
    assert args["messages"][0] == {"role": "system", "content": "you are X"}
    assert args["messages"][1] == {"role": "user", "content": "hi"}


async def test_chat_stream_yields_delta(mock_openai):
    async def fake_stream():
        yield MagicMock(choices=[MagicMock(delta=MagicMock(content="a"))])
        yield MagicMock(choices=[MagicMock(delta=MagicMock(content="b"))])
        yield MagicMock(choices=[MagicMock(delta=MagicMock(content=None))])

    mock_openai.chat.completions.create.return_value = fake_stream()
    p = OpenAIProvider(api_key="k", model="gpt-4o")
    chunks = [c async for c in p.chat_stream([{"role": "user", "content": "hi"}])]
    assert chunks == ["a", "b"]
