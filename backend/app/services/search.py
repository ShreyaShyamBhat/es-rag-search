import asyncio
from dataclasses import dataclass

from elasticsearch import AsyncElasticsearch

from app.core.config import Settings

RRF_K = 60  # standard Reciprocal Rank Fusion constant


@dataclass
class ScoredChunk:
    chunk_id: str
    doc_id: str
    filename: str
    page_number: int
    chunk_index: int
    text: str
    score: float


async def _bm25_search(es_client: AsyncElasticsearch, index: str, query_text: str, k: int):
    return await es_client.search(
        index=index,
        query={"match": {"text": query_text}},
        size=k,
        source=True,
    )


async def _knn_search(
    es_client: AsyncElasticsearch, index: str, query_vector: list[float], k: int
):
    return await es_client.search(
        index=index,
        knn={
            "field": "embedding",
            "query_vector": query_vector,
            "k": k,
            "num_candidates": max(k * 4, 100),
        },
        size=k,
        source=True,
    )


def _rrf_fuse(result_lists: list[list[dict]], top_n: int) -> list[ScoredChunk]:
    """Reciprocal Rank Fusion across multiple ranked ES hit lists.

    Native ES `retriever: {rrf: {...}}` is version/license-gated across 8.x
    minors, so fusion is done manually here for portability. This function's
    signature can stay the same if that's swapped in later.
    """
    scores: dict[str, float] = {}
    sources: dict[str, dict] = {}

    for hits in result_lists:
        for rank, hit in enumerate(hits, start=1):
            chunk_id = hit["_id"]
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (RRF_K + rank)
            sources.setdefault(chunk_id, hit["_source"])

    ranked_ids = sorted(scores, key=lambda cid: scores[cid], reverse=True)[:top_n]
    return [
        ScoredChunk(
            chunk_id=cid,
            doc_id=sources[cid]["doc_id"],
            filename=sources[cid]["filename"],
            page_number=sources[cid]["page_number"],
            chunk_index=sources[cid]["chunk_index"],
            text=sources[cid]["text"],
            score=scores[cid],
        )
        for cid in ranked_ids
    ]


async def hybrid_search(
    es_client: AsyncElasticsearch,
    settings: Settings,
    query_text: str,
    query_vector: list[float],
    k: int = 25,
) -> list[ScoredChunk]:
    bm25_response, knn_response = await asyncio.gather(
        _bm25_search(es_client, settings.es_index_name, query_text, k),
        _knn_search(es_client, settings.es_index_name, query_vector, k),
    )

    bm25_hits = bm25_response["hits"]["hits"]
    knn_hits = knn_response["hits"]["hits"]

    return _rrf_fuse([bm25_hits, knn_hits], top_n=settings.rerank_top_k)
