import json
import logging
from datetime import datetime, timezone
from typing import Any

from openai import AsyncOpenAI
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

CONDENSE_SYSTEM_PROMPT = (
    "Given a conversation history and a follow-up question, rewrite the "
    "follow-up as a single standalone question that includes any necessary "
    "context from the history. Respond with ONLY the rewritten question, "
    "no preamble."
)


def _history_key(session_id: str) -> str:
    return f"chat:session:{session_id}:history"


async def get_history(redis_client: Redis, session_id: str) -> list[dict[str, Any]]:
    raw_messages = await redis_client.lrange(_history_key(session_id), 0, -1)
    return [json.loads(m) for m in raw_messages]


async def append_message(
    redis_client: Redis,
    session_id: str,
    role: str,
    content: str,
    max_messages: int,
    ttl_seconds: int,
) -> None:
    key = _history_key(session_id)
    message = json.dumps(
        {"role": role, "content": content, "ts": datetime.now(timezone.utc).isoformat()}
    )
    await redis_client.rpush(key, message)
    await redis_client.ltrim(key, -max_messages, -1)
    await redis_client.expire(key, ttl_seconds)


async def condense_question(
    openai_client: AsyncOpenAI,
    model: str,
    history: list[dict[str, Any]],
    question: str,
) -> str:
    if not history:
        return question

    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in history)
    try:
        response = await openai_client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[
                {"role": "system", "content": CONDENSE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"History:\n{transcript}\n\nFollow-up question: {question}",
                },
            ],
        )
        condensed = (response.choices[0].message.content or "").strip()
        return condensed or question
    except Exception:
        logger.exception("Question condensing failed, using original question")
        return question
