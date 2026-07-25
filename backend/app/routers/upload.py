import logging
import uuid

from elasticsearch import AsyncElasticsearch
from elasticsearch import ApiError as ESApiError
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from openai import AsyncOpenAI, OpenAIError

from app.core.config import Settings
from app.dependencies import get_es_client, get_openai_client, get_settings_dep
from app.schemas.upload import UploadResponse
from app.services.chunker import chunk_document
from app.services.embeddings import embed_texts
from app.services.es_index import index_chunks
from app.services.pdf_processor import PDFExtractionError, extract_pages

logger = logging.getLogger(__name__)

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile,
    settings: Settings = Depends(get_settings_dep),
    es_client: AsyncElasticsearch = Depends(get_es_client),
    openai_client: AsyncOpenAI = Depends(get_openai_client),
) -> UploadResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported content type '{file.content_type}'; only application/pdf is accepted",
        )

    file_bytes = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.max_upload_mb}MB",
        )

    try:
        pages = extract_pages(file_bytes)
    except PDFExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    doc_id = str(uuid.uuid4())
    filename = file.filename or f"{doc_id}.pdf"
    chunks = chunk_document(
        doc_id=doc_id,
        filename=filename,
        pages=pages,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No text chunks could be produced from this PDF",
        )

    try:
        embeddings = await embed_texts(
            openai_client, settings.embedding_model, [c["text"] for c in chunks]
        )
    except OpenAIError as exc:
        logger.exception("OpenAI embedding request failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Embedding provider error: {exc}",
        ) from exc

    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding

    try:
        indexed_count = await index_chunks(es_client, settings, chunks)
    except ESApiError as exc:
        logger.exception("Elasticsearch indexing failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Search index error: {exc}",
        ) from exc

    return UploadResponse(
        doc_id=doc_id,
        filename=filename,
        num_pages=len(pages),
        num_chunks=indexed_count,
    )
