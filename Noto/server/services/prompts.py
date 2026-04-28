"""Prompt 模板加载 + 变量替换（内存缓存）。"""

from functools import lru_cache
from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


@lru_cache(maxsize=None)
def load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def render_prompt(name: str, **vars: str) -> str:
    tmpl = load_prompt(name)
    for k, v in vars.items():
        tmpl = tmpl.replace("{" + k + "}", v)
    return tmpl
