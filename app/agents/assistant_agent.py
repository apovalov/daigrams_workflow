import json
import os

import google.generativeai as genai


class AssistantAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    async def get_intent(self, message: str) -> dict:
        prompt = self._create_intent_prompt(message)
        response = await self.model.generate_content_async(prompt)
        return self._parse_response(response.text)

    def _create_intent_prompt(self, message: str) -> str:
        return f"""
        You are an intelligent assistant. Your job is to determine the user's intent from their message.

        Message: "{message}"

        Possible intents are:
        - "generate_diagram": The user wants to generate a diagram.
        - "clarification": The user is asking for more information or clarification.
        - "greeting": The user is just saying hello.
        - "unknown": The user's intent is unclear.

        Please respond with a JSON object containing the user's intent and any relevant entities.
        For example:
        {{
            "intent": "generate_diagram",
            "description": "Create a diagram of a web application."
        }}
        """

    def _parse_response(self, response_text: str) -> dict:
        try:
            json_text = response_text.strip().replace("```json", "").replace("```", "")
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError("Failed to decode LLM response as JSON.") from e
