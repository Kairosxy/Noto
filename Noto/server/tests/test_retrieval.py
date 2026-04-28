from unittest.mock import MagicMock

from services.retrieval import search


def test_search_returns_chunks():
    fake_supa = MagicMock()
    fake_supa.rpc.return_value.execute.return_value = MagicMock(data=[
        {"id": "c1", "document_id": "d1", "content": "hello", "page_num": 1, "distance": 0.1},
    ])
    result = search(fake_supa, notebook_id="n1", query_embedding=[0.1] * 1024, k=5)
    assert len(result) == 1
    assert result[0]["content"] == "hello"
    fake_supa.rpc.assert_called_once()
