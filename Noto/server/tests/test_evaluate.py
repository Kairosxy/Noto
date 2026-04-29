import json
from unittest.mock import AsyncMock

import pytest

from services.evaluate import evaluate_explanation


async def test_evaluate_returns_structured_feedback():
    fake = {
        "verdict": "pass",
        "feedback": "你抓住了关键。",
        "missing_points": ["可以更深一点：..."],
    }
    mock_mgr = AsyncMock()
    mock_mgr.chat = AsyncMock(return_value=json.dumps(fake))

    result = await evaluate_explanation(
        manager=mock_mgr,
        node_title="反向传播",
        node_body="利用链式法则...",
        citations="[p.42] xxx",
        user_explanation="反向传播从后往前传误差...",
    )

    assert result["verdict"] == "pass"
    assert "关键" in result["feedback"]
    assert len(result["missing_points"]) == 1


async def test_evaluate_falls_back_on_malformed_json():
    mock_mgr = AsyncMock()
    mock_mgr.chat = AsyncMock(return_value="not json at all")

    result = await evaluate_explanation(
        manager=mock_mgr,
        node_title="X", node_body="", citations="",
        user_explanation="some text",
    )
    # Fallback: treat as pass with original as feedback (don't block user)
    assert result["verdict"] == "pass"
    assert len(result["feedback"]) > 0
