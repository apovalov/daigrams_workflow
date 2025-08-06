from __future__ import annotations

import json

from app.llm import model
from app.prompts import intent_prompt

__all__ = ["AssistantAgent"]


class AssistantAgent:
    """Agent for handling assistant conversations and intent detection."""

    def __init__(self) -> None:
        pass

    async def get_intent(self, message: str) -> dict[str, str]:
        """Get intent from user message using LLM."""
        prompt = intent_prompt(message)
        response = await model.generate_content_async(prompt)
        return self._parse_response(response.text)

    def _parse_response(self, response_text: str) -> dict[str, str]:
        """Parse JSON response from LLM."""
        try:
            json_text = response_text.strip().replace("```json", "").replace("```", "")
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError("Failed to decode LLM response as JSON.") from e
