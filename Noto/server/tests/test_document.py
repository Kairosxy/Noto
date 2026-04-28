from pathlib import Path

import pytest

from services.document import parse, chunk, ParsedDoc


FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_txt():
    out = parse(FIXTURES / "sample.txt")
    assert isinstance(out, ParsedDoc)
    assert "第一段" in out.text
    assert out.pages == 1


def test_parse_pdf_extracts_pages():
    out = parse(FIXTURES / "sample.pdf")
    assert out.pages == 2
    assert "Page 1" in out.text
    assert "Page 2" in out.text
    # page_map 必须覆盖整段文本
    assert out.page_map[0]["page"] == 1
    assert out.page_map[-1]["page"] == 2


def test_parse_unknown_ext_raises(tmp_path):
    f = tmp_path / "a.xyz"
    f.write_text("hi")
    with pytest.raises(ValueError):
        parse(f)


def test_chunk_small_text_returns_single():
    doc = ParsedDoc(text="短文本。", pages=1, page_map=[{"start": 0, "end": 4, "page": 1}])
    chunks = chunk(doc, target_tokens=100)
    assert len(chunks) == 1
    assert chunks[0].content == "短文本。"
    assert chunks[0].page_num == 1
    assert chunks[0].position == 0


def test_chunk_large_text_splits_by_paragraph():
    # 模拟很长的文本，多段落
    paras = ["段落 " + str(i) + "。" * 200 for i in range(5)]
    text = "\n\n".join(paras)
    page_map = [{"start": 0, "end": len(text), "page": 1}]
    doc = ParsedDoc(text=text, pages=1, page_map=page_map)
    chunks = chunk(doc, target_tokens=100)
    assert len(chunks) >= 3
    # position 递增
    assert [c.position for c in chunks] == list(range(len(chunks)))


def test_chunk_preserves_page_num():
    # 第一段在页 1，第二段在页 2
    p1 = "第一页内容。" * 50
    p2 = "第二页内容。" * 50
    text = p1 + "\n\n" + p2
    page_map = [
        {"start": 0, "end": len(p1), "page": 1},
        {"start": len(p1) + 2, "end": len(text), "page": 2},
    ]
    doc = ParsedDoc(text=text, pages=2, page_map=page_map)
    chunks = chunk(doc, target_tokens=80)
    pages = sorted({c.page_num for c in chunks})
    assert pages == [1, 2]
