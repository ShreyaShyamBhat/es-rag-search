import json
from typing import Any


def sse_event(data: str, event: str | None = None) -> str:
    prefix = f"event: {event}\n" if event else ""
    return f"{prefix}data: {data}\n\n"


def sse_json_event(data: Any, event: str | None = None) -> str:
    return sse_event(json.dumps(data), event=event)
