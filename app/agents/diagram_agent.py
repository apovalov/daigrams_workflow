from __future__ import annotations

import json

from app.llm import model
from app.prompts import diagram_analysis_prompt

__all__ = ["DiagramAgent"]


class DiagramAgent:
    """Agent for analyzing diagram descriptions and extracting components."""

    def __init__(self) -> None:
        pass

    async def generate_analysis(
        self, description: str
    ) -> dict[str, list[dict[str, str]]]:
        """Generate diagram component analysis from description."""
        prompt = diagram_analysis_prompt(description)
        response = await model.generate_content_async(prompt)
        return self._parse_response(response.text)

    def _parse_response(self, response_text: str) -> dict[str, list[dict[str, str]]]:
        """Parse JSON response from LLM."""
        try:
            # The response may be wrapped in markdown, so we need to extract the JSON
            json_text = response_text.strip().replace("```json", "").replace("```", "")
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError("Failed to decode LLM response as JSON.") from e
