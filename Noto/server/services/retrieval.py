"""pgvector 相似度检索（第一版只做向量）"""


def search(supa, notebook_id: str, query_embedding: list[float], k: int = 5) -> list[dict]:
    r = supa.rpc("match_chunks", {
        "p_notebook_id": notebook_id,
        "p_query": query_embedding,
        "p_k": k,
    }).execute()
    return r.data or []
