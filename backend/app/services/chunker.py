from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.services.pdf_processor import PageText


def chunk_document(
    doc_id: str,
    filename: str,
    pages: list[PageText],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[dict[str, Any]]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )

    chunks: list[dict[str, Any]] = []
    chunk_index = 0
    for page in pages:
        if not page.text:
            continue
        for piece in splitter.split_text(page.text):
            if not piece.strip():
                continue
            chunks.append(
                {
                    "doc_id": doc_id,
                    "chunk_id": f"{doc_id}_{page.page_number}_{chunk_index}",
                    "filename": filename,
                    "page_number": page.page_number,
                    "chunk_index": chunk_index,
                    "text": piece,
                }
            )
            chunk_index += 1

    return chunks
