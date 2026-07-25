"""Standalone ragas evaluation script.

Runs the sample Q&A dataset against a live backend's /query SSE endpoint and
scores answer relevancy, context precision, and faithfulness. Not part of the
live API - run manually once the stack (and at least one uploaded PDF) is up:

    python eval/run_eval.py
"""

import json
import os
import time
from pathlib import Path

import httpx
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import answer_relevancy, context_precision, faithfulness

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
DATASET_PATH = Path(__file__).parent / "dataset.json"
RESULTS_DIR = Path(__file__).parent / "results"


def run_query(session_id: str, question: str) -> tuple[str, list[str]]:
    """Send a question through the SSE /query endpoint, returning the full
    answer text and the snippet texts of the sources used."""
    answer_parts: list[str] = []
    contexts: list[str] = []

    with httpx.Client(timeout=60) as client:
        with client.stream(
            "POST",
            f"{BACKEND_URL}/query",
            json={"session_id": session_id, "question": question},
        ) as response:
            response.raise_for_status()
            event_name = "message"
            data_line: str | None = None

            for line in response.iter_lines():
                if line == "":
                    if data_line is not None:
                        if event_name == "sources":
                            contexts.extend(s["snippet"] for s in json.loads(data_line))
                        elif event_name != "done":
                            answer_parts.append(json.loads(data_line))
                    event_name = "message"
                    data_line = None
                    continue
                if line.startswith("event:"):
                    event_name = line[len("event:") :].strip()
                elif line.startswith("data:"):
                    data_line = line[len("data:") :].strip()

    return "".join(answer_parts), contexts


def main() -> None:
    dataset_items = json.loads(DATASET_PATH.read_text())

    questions, answers, contexts_list, ground_truths = [], [], [], []
    for i, item in enumerate(dataset_items):
        session_id = f"eval-{i}-{int(time.time())}"
        print(f"Running: {item['question']}")
        answer, contexts = run_query(session_id, item["question"])
        questions.append(item["question"])
        answers.append(answer)
        contexts_list.append(contexts or [""])
        ground_truths.append(item["ground_truth"])

    ragas_dataset = Dataset.from_dict(
        {
            "question": questions,
            "answer": answers,
            "contexts": contexts_list,
            "ground_truth": ground_truths,
        }
    )

    result = evaluate(
        ragas_dataset,
        metrics=[answer_relevancy, context_precision, faithfulness],
    )

    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"results_{timestamp}.json"
    output_path.write_text(result.to_pandas().to_json(orient="records", indent=2))

    print("\n=== Eval Summary ===")
    print(result)
    print(f"\nDetailed results written to {output_path}")


if __name__ == "__main__":
    main()
