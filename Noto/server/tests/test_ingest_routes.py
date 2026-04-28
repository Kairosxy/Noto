from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from main import create_app


class FakeQuery:
    def __init__(self, response_data):
        self._data = response_data
    def execute(self):
        return MagicMock(data=self._data)
    def insert(self, *_a, **_kw): return self
    def update(self, *_a, **_kw): return self
    def select(self, *_a, **_kw): return self
    def eq(self, *_a, **_kw): return self
    def single(self): return self


class FakeSupabase:
    def __init__(self):
        self.tables = {}
    def table(self, name):
        return FakeQuery([])
    @property
    def storage(self):
        bucket = MagicMock()
        bucket.upload = MagicMock(return_value={"path": "notebookX/docY.pdf"})
        storage = MagicMock()
        storage.from_ = MagicMock(return_value=bucket)
        return storage


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("NOTO_AI_PROVIDER", "openai")
    monkeypatch.setenv("NOTO_AI_API_KEY", "k")
    monkeypatch.setenv("NOTO_AI_MODEL", "gpt-4o")
    monkeypatch.setenv("NOTO_EMBEDDING_MODEL", "text-embedding-3-small")
    monkeypatch.setenv("NOTO_SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("NOTO_SUPABASE_SERVICE_KEY", "srv")
    app = create_app()
    # 替换 supabase client
    app.state.supabase._client = FakeSupabase()
    return TestClient(app)


def test_upload_requires_notebook_id(client):
    resp = client.post("/api/ingest/upload", files={"file": ("x.txt", b"hi")})
    assert resp.status_code == 422  # 缺 form 字段
