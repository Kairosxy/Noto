"""Embedding 单函数。第一版只支持 openai-兼容（涵盖 OpenAI / Qwen / DeepSeek / Ollama）。

Anthropic 官方无 embedding API；Google 需要时再加分支。"""


def _get_openai_client(api_key: str, base_url: str):
    from openai import AsyncOpenAI
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return AsyncOpenAI(**kwargs)


async def embed(
    texts: list[str],
    provider: str,
    api_key: str,
    base_url: str,
    model: str,
) -> list[list[float]]:
    if not model:
        raise ValueError("embedding model 不能为空")
    if not texts:
        return []

    if provider in ("openai", "anthropic", "google"):
        # anthropic/google 也走 openai-compatible 的 /v1/embeddings 端点（用户需自备兼容端点）
        # 默认 openai 分支
        client = _get_openai_client(api_key, base_url)
        resp = await client.embeddings.create(model=model, input=texts)
        return [d.embedding for d in resp.data]

    raise ValueError(f"不支持的 embedding provider: {provider}")
