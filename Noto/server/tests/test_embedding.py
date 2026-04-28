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


async def test_embed_unknown_provider_raises():
    with pytest.raises(ValueError, match="不支持"):
        await embed(texts=["a"], provider="wat", api_key="k", base_url="", model="m")


async def test_embed_missing_model_raises():
    with pytest.raises(ValueError, match="model"):
        await embed(texts=["a"], provider="openai", api_key="k", base_url="", model="")
