"""Embedding 单函数。只走 OpenAI-兼容 API（OpenAI / Qwen / DeepSeek / Ollama / …）。

`provider` 参数仅作配置来源的标签校验 —— 实际始终用 AsyncOpenAI 发请求。
Anthropic 官方无 embedding API；Google 需要时再加分支。"""

import asyncio

# Qwen text-embedding-v3 单次最多 10 条；其他服务通常更宽松，取 10 作通用安全值。
_BATCH_SIZE = 10

_OPENAI_COMPATIBLE = {"openai", "anthropic", "google"}


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
    if provider not in _OPENAI_COMPATIBLE:
        raise ValueError(f"不支持的 embedding provider: {provider}")

    client = _get_openai_client(api_key, base_url)
    batches = [texts[i:i + _BATCH_SIZE] for i in range(0, len(texts), _BATCH_SIZE)]
    responses = await asyncio.gather(*(
        client.embeddings.create(model=model, input=batch) for batch in batches
    ))
    return [d.embedding for resp in responses for d in resp.data]
