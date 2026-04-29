"""空间/文档级蒸馏服务。所有 LLM 调用都经由 AIProviderManager。"""

import json
import logging
from pathlib import Path

from services.ai.utils import extract_json

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


async def distill_space_skeleton(
    manager,
    goal: str,
    docs_summaries: list[dict],
) -> dict:
    """输入空间目标 + 所有文档摘要，输出 JSON 骨架。"""
    if not docs_summaries:
        raise ValueError("docs_summaries 不能为空")

    prompt = (
        _load_prompt("distill_space_skeleton.md")
        .replace("{goal}", goal or "（未设定）")
        .replace("{docs_json}", json.dumps(docs_summaries, ensure_ascii=False, indent=2))
    )

    raw = await manager.chat([{"role": "user", "content": prompt}])
    parsed = extract_json(raw)
    if not isinstance(parsed, dict):
        raise ValueError(f"空间骨架解析失败，原始回复前 200 字：{raw[:200]}")

    for k in ("space_summary", "directions", "nodes"):
        if k not in parsed:
            raise ValueError(f"骨架 JSON 缺少字段 {k}")

    return parsed
