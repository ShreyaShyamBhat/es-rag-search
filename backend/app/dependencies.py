from typing import TYPE_CHECKING

from fastapi import Request

if TYPE_CHECKING:
    from elasticsearch import AsyncElasticsearch
    from openai import AsyncOpenAI
    from redis.asyncio import Redis

    from app.core.config import Settings


def get_es_client(request: Request) -> "AsyncElasticsearch":
    return request.app.state.es_client


def get_redis_client(request: Request) -> "Redis":
    return request.app.state.redis_client


def get_openai_client(request: Request) -> "AsyncOpenAI":
    return request.app.state.openai_client


def get_settings_dep(request: Request) -> "Settings":
    return request.app.state.settings
