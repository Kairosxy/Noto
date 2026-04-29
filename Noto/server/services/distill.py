"""空间/文档级蒸馏服务。所有 LLM 调用都经由 AIProviderManager。"""

import logging
from pathlib import Path

log = logging.getLogger("noto.distill")

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


async def distill_doc_summary(manager, document_text: str) -> str:
    """给定文档全文，返回三段式 markdown summary。"""
    if not document_text:
        raise ValueError("document_text 不能为空")

    prompt = _load_prompt("distill_doc_summary.md").replace("{content}", document_text)
    return await manager.chat([{"role": "user", "content": prompt}])
