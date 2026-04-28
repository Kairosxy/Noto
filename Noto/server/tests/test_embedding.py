from unittest.mock import AsyncMock, MagicMock

import pytest

from services.ai.embedding import embed


async def test_embed_openai_returns_vectors(monkeypatch):
    fake_client = MagicMock()
    fake_client.embeddings.create = AsyncMock(return_value=MagicMock(
        data=[MagicMock(embedding=[0.1, 0.2]), MagicMock(embedding=[0.3, 0.4])]
    ))
    monkeypatch.setattr(
        "services.ai.embedding._get_openai_client",
        lambda key, base_url: fake_client,
    )
    out = await embed(
        texts=["a", "b"],
        provider="openai",
        api_key="k",
        base_url="",
        model="text-embedding-3-small",
    )
    assert out == [[0.1, 0.2], [0.3, 0.4]]


async def test_embed_batches_at_10(monkeypatch):
    """Qwen text-embedding-v3 限制单次 10 条，embed 必须分批调用。"""
    calls: list[list[str]] = []

    async def fake_create(model, input):
        calls.append(list(input))
        return MagicMock(data=[MagicMock(embedding=[0.0]) for _ in input])

    fake_client = MagicMock()
    fake_client.embeddings.create = fake_create
    monkeypatch.setattr(
        "services.ai.embedding._get_openai_client",
        lambda key, base_url: fake_client,
    )
    texts = [f"t{i}" for i in range(23)]
    out = await embed(
        texts=texts,
        provider="openai",
        api_key="k",
        base_url="",
        model="text-embedding-v3",
    )
    assert len(out) == 23
    assert [len(c) for c in calls] == [10, 10, 3]


async def test_embed_unknown_provider_raises():
    with pytest.raises(ValueError, match="不支持"):
        await embed(texts=["a"], provider="wat", api_key="k", base_url="", model="m")


async def test_embed_missing_model_raises():
    with pytest.raises(ValueError, match="model"):
        await embed(texts=["a"], provider="openai", api_key="k", base_url="", model="")
