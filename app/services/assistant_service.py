from __future__ import annotations

from app.agents.assistant_agent import AssistantAgent
from app.config import Settings
from app.logging import get_logger
from app.models.diagram import AssistantResponse
from app.services.diagram_service import DiagramService

__all__ = ["AssistantService"]

logger = get_logger(__name__)


class AssistantService:
    """Service for handling assistant conversations and routing to diagram generation."""

    def __init__(self, settings: Settings) -> None:
        self.assistant_agent = AssistantAgent()
        self.diagram_service = DiagramService(settings)

    async def process_message(self, message: str) -> AssistantResponse:
        intent_data = await self.assistant_agent.get_intent(message)
        intent = intent_data.get("intent")

        if intent == "generate_diagram":
            description = intent_data.get("description")
            if not description:
                return AssistantResponse(
                    response_type="question",
                    content="I can help with that! What would you like the diagram to show?",
                )

            (
                image_data,
                _,
            ) = await self.diagram_service.generate_diagram_from_description(
                description
            )
            return AssistantResponse(
                response_type="image",
                content="Here is the diagram you requested:",
                image_data=image_data,
            )
        elif intent == "clarification":
            return AssistantResponse(
                response_type="text",
                content="I am an AI assistant that can generate diagrams from natural language descriptions. How can I help you?",
            )
        elif intent == "greeting":
            return AssistantResponse(
                response_type="text",
                content="Hello! How can I help you create a diagram today?",
            )
        else:
            return AssistantResponse(
                response_type="text",
                content="I'm not sure how to help with that. Please try describing the diagram you would like to create.",
            )
