import logging

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException

from app.models.diagram import (
    AssistantRequest,
    AssistantResponse,
    DiagramMetadata,
    DiagramRequest,
    DiagramResponse,
)
from app.services.assistant_service import AssistantService
from app.services.diagram_service import DiagramService

# Load environment variables from .env file
load_dotenv()

app = FastAPI()
logger = logging.getLogger(__name__)


def get_diagram_service():
    return DiagramService()


def get_assistant_service():
    return AssistantService()


@app.post("/api/v1/generate-diagram", response_model=DiagramResponse)
async def generate_diagram(
    request: DiagramRequest,
    diagram_service: DiagramService = Depends(get_diagram_service),
):
    """
    Generate diagram image from natural language description.
    """
    if not request.description:
        raise HTTPException(
            status_code=400, detail="Invalid diagram description provided"
        )

    try:
        image_data, metadata = await diagram_service.generate_diagram_from_description(
            request.description
        )

        return DiagramResponse(
            success=True, image_data=image_data, metadata=DiagramMetadata(**metadata)
        )
    except Exception as e:
        logger.error(f"Error generating diagram: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/assistant", response_model=AssistantResponse)
async def assistant(
    request: AssistantRequest,
    assistant_service: AssistantService = Depends(get_assistant_service),
):
    """
    Assistant-style endpoint with context awareness.
    """
    if not request.message:
        raise HTTPException(status_code=400, detail="Invalid message provided")

    return await assistant_service.process_message(request.message)
