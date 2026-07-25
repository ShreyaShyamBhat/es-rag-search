import json
import logging

from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from app.services.search import ScoredChunk

logger = logging.getLogger(__name__)

MAX_EXCERPT_CHARS = 500

RERANK_SYSTEM_PROMPT = (
    "You are a relevance grading assistant. Given a question and a numbered list "
    "of text excerpts, score each excerpt from 0 to 10 on how directly and "
    "completely it helps answer the question. Respond with ONLY a JSON object "
    'of the form {"scores": [{"index": 1, "score": 8}, ...]} covering every '
    "excerpt index exactly once. Do not include any other text."
)


class _ScoreEntry(BaseModel):
    index: int
    score: float


class _RerankScores(BaseModel):
    scores: list[_ScoreEntry]


def _build_user_prompt(question: str, candidates: list[ScoredChunk]) -> str:
    lines = [f"Question: {question}", "", "Excerpts:"]
    for i, chunk in enumerate(candidates, start=1):
        excerpt = chunk.text[:MAX_EXCERPT_CHARS]
        lines.append(f"[{i}] (page {chunk.page_number}) {excerpt}")
    return "\n".join(lines)


async def rerank(
    client: AsyncOpenAI,
    model: str,
    question: str,
    candidates: list[ScoredChunk],
    top_k: int = 3,
) -> list[ScoredChunk]:
    if not candidates:
        return []

    fallback = candidates[:top_k]

    try:
        response = await client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": RERANK_SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(question, candidates)},
            ],
            temperature=0,
        )
        raw = response.choices[0].message.content or ""
        parsed = _RerankScores.model_validate(json.loads(raw))
    except (json.JSONDecodeError, ValidationError, KeyError, IndexError) as exc:
        logger.warning("Rerank response parsing failed, falling back to RRF order: %s", exc)
        return fallback
    except Exception:
        logger.exception("Rerank LLM call failed, falling back to RRF order")
        return fallback

    valid_entries = [
        entry for entry in parsed.scores if 1 <= entry.index <= len(candidates)
    ]
    if not valid_entries:
        logger.warning("Rerank response had no valid indices, falling back to RRF order")
        return fallback

    ranked = sorted(valid_entries, key=lambda e: e.score, reverse=True)
    return [candidates[entry.index - 1] for entry in ranked[:top_k]]
