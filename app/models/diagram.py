from __future__ import annotations

from pydantic import BaseModel

__all__ = [
    "DiagramRequest",
    "DiagramMetadata",
    "DiagramResponse",
    "AssistantRequest",
    "AssistantResponse",
]


class DiagramRequest(BaseModel):
    description: str
    format: str | None = "png"
    style: str | None = None
    size: dict[str, str] | None = None


class DiagramMetadata(BaseModel):
    nodes_created: int
    clusters_created: int
    connections_made: int
    generation_time: float


class DiagramResponse(BaseModel):
    success: bool
    image_data: str | None = None
    image_url: str | None = None
    metadata: DiagramMetadata | None = None


class AssistantRequest(BaseModel):
    message: str
    context: dict[str, str] | None = None
    conversation_id: str | None = None


class AssistantResponse(BaseModel):
    response_type: str
    content: str
    image_data: str | None = None
    follow_up_questions: list[str] | None = None
    suggestions: list[str] | None = None
