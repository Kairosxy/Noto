import json
from unittest.mock import AsyncMock

import pytest

from services.distill import distill_space_skeleton


async def test_distill_space_skeleton_parses_llm_json(monkeypatch):
    fake_json = {
        "space_summary": "A space summary",
        "directions": [
            {
                "position": 0,
                "title": "核心方向",
                "description": "desc",
                "estimated_minutes": 12,
                "node_ids": ["c1"],
            }
        ],
        "nodes": [
            {
                "temp_id": "c1",
                "node_type": "claim",
                "title": "一条主张",
                "body": None,
                "source_positions": [{"document_id": "doc1", "chunk_id": "chunk1", "page_num": 42}],
            }
        ],
    }

    mock_mgr = AsyncMock()
    mock_mgr.chat = AsyncMock(return_value=json.dumps(fake_json))

    result = await distill_space_skeleton(
        manager=mock_mgr,
        goal="学懂反向传播",
        docs_summaries=[
            {"document_id": "doc1", "title": "第3章", "summary": "summary"},
        ],
    )

    assert result["space_summary"] == "A space summary"
    assert len(result["directions"]) == 1
    assert result["directions"][0]["title"] == "核心方向"
    assert len(result["nodes"]) == 1


async def test_distill_space_skeleton_raises_on_invalid_json():
    mock_mgr = AsyncMock()
    mock_mgr.chat = AsyncMock(return_value="this is not JSON")

    with pytest.raises(ValueError, match="解析"):
        await distill_space_skeleton(
            manager=mock_mgr,
            goal="g",
            docs_summaries=[{"document_id": "d", "title": "t", "summary": "s"}],
        )


async def test_distill_space_skeleton_empty_docs_raises():
    mock_mgr = AsyncMock()
    with pytest.raises(ValueError, match="docs"):
        await distill_space_skeleton(
            manager=mock_mgr,
            goal="g",
            docs_summaries=[],
        )
