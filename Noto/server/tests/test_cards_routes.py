from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from main import create_app


class FakeQ:
    def __init__(self, data): self._d = data
    def execute(self): return MagicMock(data=self._d)
    def eq(self, *a, **kw): return self
    def update(self, *a, **kw): return self
    def select(self, *a, **kw): return self
    def insert(self, *a, **kw): return self
    def single(self): return self
    def in_(self, *a, **kw): return self
    def order(self, *a, **kw): return self


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("NOTO_AI_PROVIDER", "openai")
    monkeypatch.setenv("NOTO_AI_API_KEY", "k")
    monkeypatch.setenv("NOTO_AI_MODEL", "gpt-4o")
    monkeypatch.setenv("NOTO_SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("NOTO_SUPABASE_SERVICE_KEY", "s")
    app = create_app()

    fake_supa = MagicMock()
    fake_supa.table = MagicMock(return_value=FakeQ([{"id": "cardX", "card_state": "got_it"}]))
    app.state.supabase._client = fake_supa
    return TestClient(app)


def test_update_state_to_thinking(client):
    resp = client.patch("/api/cards/cardX/state", json={"state": "thinking"})
    assert resp.status_code == 200


def test_update_state_got_it_requires_explanation(client):
    resp = client.patch("/api/cards/cardX/state", json={"state": "got_it"})
    assert resp.status_code == 400
    assert "user_explanation" in resp.json()["detail"]


def test_update_state_got_it_with_explanation(client):
    resp = client.patch("/api/cards/cardX/state", json={
        "state": "got_it",
        "user_explanation": "我的理解是...",
    })
    assert resp.status_code == 200
