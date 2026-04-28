"""文档解析 + 分块"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParsedDoc:
    text: str
    pages: int
    # [{"start": char_offset, "end": char_offset, "page": n}]
    page_map: list[dict]


@dataclass
class Chunk:
    content: str
    page_num: int
    position: int


def _sanitize(s: str) -> str:
    # Postgres text 拒绝 NUL；某些 PDF 解析器会漏 NUL 字节
    return s.replace("\x00", "")


def parse(path: Path | str) -> ParsedDoc:
    p = Path(path)
    ext = p.suffix.lower()

    if ext == ".txt" or ext == ".md":
        text = _sanitize(p.read_text(encoding="utf-8"))
        return ParsedDoc(text=text, pages=1, page_map=[{"start": 0, "end": len(text), "page": 1}])

    if ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(p))
        parts = []
        page_map = []
        cursor = 0
        for i, page in enumerate(reader.pages, start=1):
            page_text = _sanitize(page.extract_text() or "")
            if cursor > 0:
                parts.append("\n\n")
                cursor += 2
            parts.append(page_text)
            page_map.append({"start": cursor, "end": cursor + len(page_text), "page": i})
            cursor += len(page_text)
        return ParsedDoc(text="".join(parts), pages=len(reader.pages), page_map=page_map)

    if ext == ".docx":
        from docx import Document
        doc = Document(str(p))
        text = _sanitize("\n\n".join(pa.text for pa in doc.paragraphs if pa.text.strip()))
        return ParsedDoc(text=text, pages=1, page_map=[{"start": 0, "end": len(text), "page": 1}])

    raise ValueError(f"不支持的文件类型: {ext}")


def _page_for_offset(offset: int, page_map: list[dict]) -> int:
    for m in page_map:
        if m["start"] <= offset < m["end"]:
            return m["page"]
    return page_map[-1]["page"] if page_map else 1


def _estimate_tokens(s: str) -> int:
    # 粗估：1 token ≈ 0.7 个中英字符（粗糙但无依赖）
    return max(1, int(len(s) / 0.7))


def chunk(doc: ParsedDoc, target_tokens: int = 800) -> list[Chunk]:
    """按段落切，超目标则硬切。不做 overlap / heading-aware。"""
    paragraphs = [p for p in doc.text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    chunks: list[Chunk] = []
    buffer = ""
    buffer_start = 0
    cursor = 0
    position = 0

    def emit():
        nonlocal buffer, buffer_start, position
        if not buffer.strip():
            return
        page = _page_for_offset(buffer_start, doc.page_map)
        chunks.append(Chunk(content=buffer.strip(), page_num=page, position=position))
        position += 1
        buffer = ""

    for para in paragraphs:
        para_start = doc.text.find(para, cursor)
        if para_start == -1:
            para_start = cursor
        cursor = para_start + len(para)

        if _estimate_tokens(para) > target_tokens:
            emit()
            step = int(target_tokens * 0.7)
            for i in range(0, len(para), step):
                seg = para[i:i + step]
                page = _page_for_offset(para_start + i, doc.page_map)
                chunks.append(Chunk(content=seg, page_num=page, position=position))
                position += 1
            continue

        if buffer and _estimate_tokens(buffer) + _estimate_tokens(para) > target_tokens:
            emit()
            buffer_start = para_start

        if not buffer:
            buffer_start = para_start
        buffer = (buffer + "\n\n" + para) if buffer else para

    emit()
    return chunks
