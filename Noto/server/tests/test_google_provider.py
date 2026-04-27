from unittest.mock import AsyncMock, MagicMock

import pytest

from services.ai.google_provider import GoogleProvider


@pytest.fixture
def mock_google(monkeypatch):
    client = MagicMock()
    client.aio.models.generate_content = AsyncMock()
    monkeypatch.setattr(
        "services.ai.google_provider.GoogleProvider._get_client",
        lambda self: client,
    )
    return client


async def test_chat_returns_text(mock_google):
    mock_google.aio.models.generate_content.return_value = MagicMock(text="hi")
    p = GoogleProvider(api_key="k", model="gemini-2.5-flash")
    result = await p.chat([{"role": "user", "content": "hi"}])
    assert result == "hi"


async def test_chat_converts_role_assistant_to_model(mock_google):
    mock_google.aio.models.generate_content.return_value = MagicMock(text="")
    p = GoogleProvider(api_key="k", model="gemini-2.5-flash")
    await p.chat([
        {"role": "user", "content": "q"},
        {"role": "assistant", "content": "a"},
    ])
    contents = mock_google.aio.models.generate_content.call_args.kwargs["contents"]
    assert contents[0]["role"] == "user"
    assert contents[1]["role"] == "model"
