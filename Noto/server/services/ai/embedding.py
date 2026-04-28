"""Embedding 单函数。第一版只支持 openai-兼容（涵盖 OpenAI / Qwen / DeepSeek / Ollama）。

Anthropic 官方无 embedding API；Google 需要时再加分支。"""


# Qwen text-embedding-v3 limits batch to 10; others usually allow more.
# 10 is safe universally.
_BATCH_SIZE = 10


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
        client = _get_openai_client(api_key, base_url)
        vectors: list[list[float]] = []
        for i in range(0, len(texts), _BATCH_SIZE):
            batch = texts[i:i + _BATCH_SIZE]
            resp = await client.embeddings.create(model=model, input=batch)
            vectors.extend(d.embedding for d in resp.data)
        return vectors

    raise ValueError(f"不支持的 embedding provider: {provider}")
