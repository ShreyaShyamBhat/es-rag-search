import logging

from elasticsearch import AsyncElasticsearch
from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from app.dependencies import get_es_client, get_redis_client
from app.schemas.common import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(
    es_client: AsyncElasticsearch = Depends(get_es_client),
    redis_client: Redis = Depends(get_redis_client),
) -> HealthResponse:
    es_status = "ok"
    try:
        await es_client.cluster.health()
    except Exception:
        logger.exception("Elasticsearch health check failed")
        es_status = "unavailable"

    redis_status = "ok"
    try:
        await redis_client.ping()
    except Exception:
        logger.exception("Redis health check failed")
        redis_status = "unavailable"

    overall = "ok" if es_status == "ok" and redis_status == "ok" else "degraded"
    return HealthResponse(status=overall, elasticsearch=es_status, redis=redis_status)
