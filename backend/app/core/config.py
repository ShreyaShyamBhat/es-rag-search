from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # OpenAI
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4"

    # Elasticsearch
    es_host: str = "http://localhost:9200"
    es_index_name: str = "documents"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    memory_ttl_seconds: int = 3600
    memory_max_messages: int = 10  # last 5 exchanges (user+assistant)

    # CORS
    allowed_origins: str = "http://localhost:5173"

    # Chunking
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Retrieval / reranking
    rerank_top_k: int = 10
    final_top_k: int = 3

    # Upload limits
    max_upload_mb: int = 25

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
