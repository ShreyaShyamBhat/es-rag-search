import logging
from collections.abc import AsyncGenerator

from elasticsearch import AsyncElasticsearch
from openai import AsyncOpenAI
from redis.asyncio import Redis

from app.core.config import Settings
from app.schemas.query import SourceItem
from app.services.embeddings import embed_texts
from app.services.memory import append_message, condense_question, get_history
from app.services.rerank import rerank
from app.services.search import ScoredChunk, hybrid_search
from app.utils.sse import sse_json_event

logger = logging.getLogger(__name__)

ANSWER_SYSTEM_PROMPT = (
    "You are a document Q&A assistant. Answer the question using ONLY the "
    "provided excerpts. Cite every factual claim inline like [Source N, p.X]. "
    "If the excerpts don't contain the answer, say so plainly instead of "
    "guessing."
)

SNIPPET_CHARS = 300


def _build_answer_prompt(question: str, sources: list[ScoredChunk]) -> str:
    lines = [f"Question: {question}", "", "Excerpts:"]
    for i, chunk in enumerate(sources, start=1):
        lines.append(f"Source {i} (page {chunk.page_number}): {chunk.text}")
    return "\n\n".join(lines)


async def run_query(
    es_client: AsyncElasticsearch,
    redis_client: Redis,
    openai_client: AsyncOpenAI,
    settings: Settings,
    session_id: str,
    question: str,
) -> AsyncGenerator[str, None]:
    history = await get_history(redis_client, session_id)
    standalone_question = await condense_question(
        openai_client, settings.llm_model, history, question
    )

    try:
        [query_vector] = await embed_texts(
            openai_client, settings.embedding_model, [standalone_question]
        )
        candidates = await hybrid_search(
            es_client, settings, standalone_question, query_vector, k=25
        )
        top_sources = await rerank(
            openai_client,
            settings.llm_model,
            standalone_question,
            candidates,
            top_k=settings.final_top_k,
        )
    except Exception:
        logger.exception("Retrieval/rerank failed for session %s", session_id)
        yield sse_json_event("Sorry, something went wrong while searching your documents.")
        yield sse_json_event({}, event="done")
        return

    if not top_sources:
        yield sse_json_event("I couldn't find any relevant content in the uploaded documents.")
        yield sse_json_event([], event="sources")
        yield sse_json_event({}, event="done")
        await append_message(
            redis_client, session_id, "user", question,
            settings.memory_max_messages, settings.memory_ttl_seconds,
        )
        return

    prompt = _build_answer_prompt(standalone_question, top_sources)
    answer_parts: list[str] = []

    stream = await openai_client.chat.completions.create(
        model=settings.llm_model,
        temperature=0,
        stream=True,
        messages=[
            {"role": "system", "content": ANSWER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            answer_parts.append(delta)
            yield sse_json_event(delta)

    full_answer = "".join(answer_parts)

    await append_message(
        redis_client, session_id, "user", question,
        settings.memory_max_messages, settings.memory_ttl_seconds,
    )
    await append_message(
        redis_client, session_id, "assistant", full_answer,
        settings.memory_max_messages, settings.memory_ttl_seconds,
    )

    source_items = [
        SourceItem(
            chunk_id=chunk.chunk_id,
            filename=chunk.filename,
            page_number=chunk.page_number,
            snippet=chunk.text[:SNIPPET_CHARS],
        ).model_dump()
        for chunk in top_sources
    ]
    yield sse_json_event(source_items, event="sources")
    yield sse_json_event({}, event="done")
