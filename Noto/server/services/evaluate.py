"""AI 评判用户"懂了"的解释（质性，非打分）。"""

import logging
from pathlib import Path

from services.ai.utils import extract_json

log = logging.getLogger("noto.evaluate")

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "evaluate_explanation.md"


async def evaluate_explanation(
    manager,
    node_title: str,
    node_body: str,
    citations: str,
    user_explanation: str,
) -> dict:
    """返回 {verdict, feedback, missing_points}。解析失败时温和降级为 pass。"""
    prompt = (
        _PROMPT_PATH.read_text(encoding="utf-8")
        .replace("{node_title}", node_title)
        .replace("{node_body}", node_body or "")
        .replace("{citations}", citations or "（无相关引用）")
        .replace("{user_explanation}", user_explanation)
    )

    raw = await manager.chat([{"role": "user", "content": prompt}])
    parsed = extract_json(raw)

    if (
        isinstance(parsed, dict)
        and parsed.get("verdict") in ("pass", "can_deepen")
        and "feedback" in parsed
    ):
        parsed.setdefault("missing_points", [])
        return parsed

    log.warning("evaluate_explanation parse fallback; raw=%s", raw[:120])
    return {
        "verdict": "pass",
        "feedback": raw.strip()[:200] or "AI 未返回结构化反馈，但你的解释已被接收。",
        "missing_points": [],
    }
