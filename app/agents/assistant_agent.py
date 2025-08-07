from __future__ import annotations

import json

from app.config import settings
from app.llm import client
from app.prompts import intent_prompt

__all__ = ["AssistantAgent"]


class AssistantAgent:
    """Agent for handling assistant conversations and intent detection."""

    def __init__(self) -> None:
        pass

    async def get_intent(
        self, message: str, context: dict | None = None
    ) -> dict[str, str]:
        """Get intent from user message using LLM."""
        # Include context in prompt if available
        context_str = ""
        if context and "messages" in context and len(context["messages"]) > 1:
            recent_messages = context["messages"][-3:]  # Last 3 messages for context
            context_str = f"\nConversation history: {recent_messages}"

        prompt = intent_prompt(message + context_str)
        try:
            response = await client.aio.models.generate_content(
                model=settings.gemini_model, contents=prompt
            )
            return self._parse_response(response.text or "")
        except Exception as e:
            # If there's a location or API issue, return a basic fallback
            if "location" in str(e).lower() or "failed_precondition" in str(e).lower():
                return self._create_fallback_intent(message)
            raise e

    def _create_fallback_intent(self, message: str) -> dict[str, str]:
        """Create a basic fallback intent when API is unavailable."""
        # Simple heuristics to determine intent
        message_lower = message.lower()
        if any(
            word in message_lower
            for word in ["create", "generate", "diagram", "draw", "build"]
        ):
            return {"intent": "generate_diagram", "confidence": "medium"}
        elif any(word in message_lower for word in ["help", "how", "what", "explain"]):
            return {"intent": "help", "confidence": "medium"}
        else:
            return {"intent": "general", "confidence": "low"}

    def _parse_response(self, response_text: str) -> dict[str, str]:
        """Parse JSON response from LLM."""
        try:
            json_text = response_text.strip().replace("```json", "").replace("```", "")
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError("Failed to decode LLM response as JSON.") from e
