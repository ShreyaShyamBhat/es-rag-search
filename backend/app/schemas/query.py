from pydantic import BaseModel


class QueryRequest(BaseModel):
    session_id: str
    question: str


class SourceItem(BaseModel):
    chunk_id: str
    filename: str
    page_number: int
    snippet: str
