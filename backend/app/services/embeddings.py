from openai import AsyncOpenAI

from app.utils.retry import openai_retry

BATCH_SIZE = 100


@openai_retry
async def _embed_batch(client: AsyncOpenAI, model: str, batch: list[str]) -> list[list[float]]:
    response = await client.embeddings.create(model=model, input=batch)
    return [item.embedding for item in response.data]


async def embed_texts(
    client: AsyncOpenAI,
    model: str,
    texts: list[str],
    batch_size: int = BATCH_SIZE,
) -> list[list[float]]:
    """Embed texts in batches, preserving input order."""
    embeddings: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        embeddings.extend(await _embed_batch(client, model, batch))
    return embeddings
