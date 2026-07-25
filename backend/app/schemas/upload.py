from pydantic import BaseModel


class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    num_pages: int
    num_chunks: int
