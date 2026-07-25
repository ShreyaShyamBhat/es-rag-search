import logging
from contextlib import asynccontextmanager

from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.routers import health, query, upload
from app.services.es_index import ensure_index

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings

    app.state.es_client = AsyncElasticsearch(hosts=[settings.es_host])
    app.state.redis_client = Redis(
        host=settings.redis_host, port=settings.redis_port, decode_responses=True
    )
    app.state.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    try:
        await ensure_index(app.state.es_client, settings)
        logger.info("Elasticsearch index '%s' ready", settings.es_index_name)
    except Exception:
        logger.exception("Failed to ensure Elasticsearch index at startup")

    yield

    await app.state.es_client.close()
    await app.state.redis_client.aclose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="ES RAG Document Q&A", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(upload.router)
    app.include_router(query.router)

    return app


app = create_app()
