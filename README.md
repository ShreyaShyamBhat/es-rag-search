# Elasticsearch + Vector RAG Document Q&A

Hybrid search (BM25 keyword + kNN semantic, fused via RRF) with LLM reranking over uploaded PDFs. FastAPI backend, React/Vite/Tailwind frontend, Elasticsearch 8.x, Redis for conversation memory, OpenAI for embeddings + generation.

## Stack

- Elasticsearch 8.x (dense_vector + BM25)
- FastAPI (Python 3.11+, async)
- LangChain (`RecursiveCharacterTextSplitter`)
- OpenAI `text-embedding-3-small` + `gpt-4`
- Redis (session memory)
- React + Vite + Tailwind
- Docker Compose

## Quick start

```bash
cp .env.example .env
# edit .env and set OPENAI_API_KEY

docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000 (docs at `/docs`)
- Elasticsearch: http://localhost:9200

## Architecture

1. **Upload** (`POST /upload`): PDF → `pdfplumber` text extraction (per page) → `RecursiveCharacterTextSplitter` (1000 chars / 200 overlap, page-aware) → batched OpenAI embeddings → bulk indexed into Elasticsearch (`text` + `dense_vector` fields).
2. **Query** (`POST /query`, SSE): optional Redis-backed history is condensed with the new question into a standalone query → embedded → hybrid search (BM25 `match` + `knn`, fused with manual Reciprocal Rank Fusion) → top ~10 candidates reranked by GPT-4 (JSON-scored) → top 3 passed to an answer-generation prompt → tokens streamed to the client via SSE, followed by a structured `sources` event for citations.
3. **Memory**: last 5 exchanges per `session_id` stored in Redis, used to contextualize follow-up questions.
4. **Eval**: `eval/run_eval.py` runs a sample Q&A dataset through the live API and scores answer relevancy, context precision, and faithfulness with `ragas`, logging results to `eval/results/`.

## Development without Docker

Backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Requires local Elasticsearch and Redis reachable at the hosts configured in `.env`.

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Eval

```bash
python eval/run_eval.py
```
Requires the backend to be running and reachable; writes metrics to `eval/results/`.
