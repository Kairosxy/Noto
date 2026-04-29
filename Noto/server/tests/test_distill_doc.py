from unittest.mock import AsyncMock

import pytest

from services.distill import distill_doc_summary


async def test_distill_doc_summary_loads_prompt_and_calls_llm(monkeypatch):
    fake_llm_response = """## 核心论点
这是核心论点。

## 主要脉络
- A
- B

## 关键结论
- X"""

    mock_mgr = AsyncMock()
    mock_mgr.chat = AsyncMock(return_value=fake_llm_response)

    result = await distill_doc_summary(
        manager=mock_mgr,
        document_text="some long document content",
    )

    assert "核心论点" in result
    assert "这是核心论点" in result
    mock_mgr.chat.assert_called_once()
    # Confirm prompt interpolation happened
    call_args = mock_mgr.chat.call_args
    user_msg = call_args[0][0][0]["content"]
    assert "some long document content" in user_msg


async def test_distill_doc_summary_empty_text_raises():
    mock_mgr = AsyncMock()
    with pytest.raises(ValueError, match="document_text"):
        await distill_doc_summary(manager=mock_mgr, document_text="")
