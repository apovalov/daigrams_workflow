from pydantic import BaseModel
from typing import Optional, List

class DiagramRequest(BaseModel):
    description: str
    format: Optional[str] = "png"
    style: Optional[str] = None
    size: Optional[dict] = None

class DiagramMetadata(BaseModel):
    nodes_created: int
    clusters_created: int
    connections_made: int
    generation_time: float

class DiagramResponse(BaseModel):
    success: bool
    image_data: Optional[str] = None
    image_url: Optional[str] = None
    metadata: Optional[DiagramMetadata] = None

class AssistantRequest(BaseModel):
    message: str
    context: Optional[dict] = None
    conversation_id: Optional[str] = None

class AssistantResponse(BaseModel):
    response_type: str
    content: str
    image_data: Optional[str] = None
    follow_up_questions: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None
