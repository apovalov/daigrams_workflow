from __future__ import annotations

from app.agents.assistant_agent import AssistantAgent
from app.config import Settings
from app.logging import get_logger
from app.models.diagram import AssistantRequest, AssistantResponse
from app.services.diagram_service import DiagramService

__all__ = ["AssistantService"]

logger = get_logger(__name__)


class AssistantService:
    """Service for handling assistant conversations and routing to diagram generation."""

    def __init__(self, settings: Settings) -> None:
        self.assistant_agent = AssistantAgent()
        self.diagram_service = DiagramService(settings)
        # Simple in-memory conversation store (for stateless service with session-like behavior)
        self._conversation_context: dict[str, dict] = {}

    async def process_message(self, request: AssistantRequest) -> AssistantResponse:
        # Handle conversation context and memory
        conversation_id = request.conversation_id or "default"
        context = self._get_conversation_context(conversation_id)

        # Add current message to context
        if "messages" not in context:
            context["messages"] = []
        context["messages"].append({"role": "user", "content": request.message})

        # Include context in intent detection if available
        message_with_context = request.message
        if request.context:
            context.update(request.context)

        intent_data = await self.assistant_agent.get_intent(
            message_with_context, context
        )
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
            response = AssistantResponse(
                response_type="image",
                content="Here is the diagram you requested:",
                image_data=image_data,
                follow_up_questions=[
                    "Would you like me to modify any part of this diagram?",
                    "Should I explain how this architecture works?",
                ],
            )

            # Store response in context
            context["messages"].append(
                {"role": "assistant", "content": response.content, "type": "image"}
            )
            self._update_conversation_context(conversation_id, context)
            return response
        elif intent == "clarification":
            response = AssistantResponse(
                response_type="text",
                content="I am an AI assistant that can generate diagrams from natural language descriptions. How can I help you?",
                suggestions=[
                    "Create a system architecture diagram",
                    "Generate a microservices diagram",
                    "Design a web application flow",
                ],
            )
        elif intent == "greeting":
            response = AssistantResponse(
                response_type="text",
                content="Hello! How can I help you create a diagram today?",
                suggestions=[
                    "Show me an example diagram",
                    "Create a cloud architecture",
                    "Design a database schema",
                ],
            )
        else:
            response = AssistantResponse(
                response_type="text",
                content="I'm not sure how to help with that. Please try describing the diagram you would like to create.",
                suggestions=[
                    "Try: 'Create a web application with database'",
                    "Try: 'Show me a microservices architecture'",
                ],
            )

        # Store response in context
        context["messages"].append({"role": "assistant", "content": response.content})
        self._update_conversation_context(conversation_id, context)
        return response

    def _get_conversation_context(self, conversation_id: str) -> dict:
        """Get conversation context for a given conversation ID."""
        return self._conversation_context.get(conversation_id, {})

    def _update_conversation_context(self, conversation_id: str, context: dict) -> None:
        """Update conversation context for a given conversation ID."""
        # Keep only last 10 messages to prevent memory bloat
        if "messages" in context and len(context["messages"]) > 10:
            context["messages"] = context["messages"][-10:]
        self._conversation_context[conversation_id] = context
