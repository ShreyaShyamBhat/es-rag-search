from elasticsearch import AsyncElasticsearch
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from redis.asyncio import Redis

from app.core.config import Settings
from app.dependencies import (
    get_es_client,
    get_openai_client,
    get_redis_client,
    get_settings_dep,
)
from app.schemas.query import QueryRequest
from app.services.rag_pipeline import run_query

router = APIRouter(tags=["query"])


@router.post("/query")
async def query(
    request: QueryRequest,
    settings: Settings = Depends(get_settings_dep),
    es_client: AsyncElasticsearch = Depends(get_es_client),
    redis_client: Redis = Depends(get_redis_client),
    openai_client: AsyncOpenAI = Depends(get_openai_client),
) -> StreamingResponse:
    generator = run_query(
        es_client,
        redis_client,
        openai_client,
        settings,
        request.session_id,
        request.question,
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
