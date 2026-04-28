from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from main import create_app


@pytest.fixture
def client(monkeypatch):
    # 绕过真实 AI 调用
    monkeypatch.setenv("NOTO_AI_PROVIDER", "openai")
    monkeypatch.setenv("NOTO_AI_API_KEY", "k")
    monkeypatch.setenv("NOTO_AI_MODEL", "gpt-4o")
    app = create_app()
    return TestClient(app)


def test_test_connection_uses_saved_key(client, monkeypatch):
    from services.ai.manager import AIProviderManager
    monkeypatch.setattr(
        AIProviderManager,
        "test_with_params",
        AsyncMock(return_value={"success": True, "message": "ok"}),
    )
    resp = client.post("/api/ai/test-connection", json={
        "provider": "openai",
        "api_key": "__use_saved__",
        "model": "gpt-4o",
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_settings_get_hides_keys(client):
    resp = client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_api_key_set"] is True
    assert "ai_api_key" not in data


def test_chat_streams_sse(client, monkeypatch):
    from services.ai.manager import AIProviderManager

    async def fake_stream(self, messages, system=""):
        for c in ["a", "b", "c"]:
            yield c
    monkeypatch.setattr(AIProviderManager, "chat_stream", fake_stream)

    with client.stream("POST", "/api/ai/chat", json={
        "messages": [{"role": "user", "content": "hi"}],
        "system": "",
    }) as resp:
        assert resp.status_code == 200
        body = b"".join(resp.iter_bytes()).decode()
    assert "\"content\": \"a\"" in body
    assert "\"content\": \"b\"" in body
    assert "[DONE]" in body
