from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: str
    elasticsearch: str
    redis: str
