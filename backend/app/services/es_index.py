import logging
from datetime import datetime, timezone
from typing import Any

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from app.core.config import Settings

logger = logging.getLogger(__name__)

EMBEDDING_DIMS = 1536  # text-embedding-3-small

INDEX_MAPPING: dict[str, Any] = {
    "settings": {
        "index": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        }
    },
    "mappings": {
        "properties": {
            "doc_id": {"type": "keyword"},
            "chunk_id": {"type": "keyword"},
            "filename": {"type": "keyword"},
            "page_number": {"type": "integer"},
            "chunk_index": {"type": "integer"},
            "text": {"type": "text", "analyzer": "english"},
            "embedding": {
                "type": "dense_vector",
                "dims": EMBEDDING_DIMS,
                "index": True,
                "similarity": "cosine",
                "index_options": {
                    "type": "hnsw",
                    "m": 16,
                    "ef_construction": 100,
                },
            },
            "created_at": {"type": "date"},
        }
    },
}


async def ensure_index(es_client: AsyncElasticsearch, settings: Settings) -> None:
    exists = await es_client.indices.exists(index=settings.es_index_name)
    if exists:
        return
    await es_client.indices.create(index=settings.es_index_name, body=INDEX_MAPPING)
    logger.info("Created Elasticsearch index '%s'", settings.es_index_name)


async def index_chunks(
    es_client: AsyncElasticsearch,
    settings: Settings,
    chunks: list[dict[str, Any]],
) -> int:
    """Bulk-index chunk documents. Each chunk dict must already contain an
    'embedding' key (list[float]) alongside doc_id/chunk_id/filename/page_number/
    chunk_index/text.
    """
    now = datetime.now(timezone.utc).isoformat()
    actions = [
        {
            "_index": settings.es_index_name,
            "_id": chunk["chunk_id"],
            "_source": {**chunk, "created_at": now},
        }
        for chunk in chunks
    ]
    success_count, errors = await async_bulk(es_client, actions, raise_on_error=False)
    if errors:
        logger.error("Bulk index encountered %d errors: %s", len(errors), errors[:3])
    return success_count


async def delete_document(es_client: AsyncElasticsearch, settings: Settings, doc_id: str) -> None:
    await es_client.delete_by_query(
        index=settings.es_index_name,
        body={"query": {"term": {"doc_id": doc_id}}},
    )
