import google.generativeai as genai
import os
import json

class DiagramAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def generate_analysis(self, description: str) -> dict:
        prompt = self._create_prompt(description)
        response = await self.model.generate_content_async(prompt)
        return self._parse_response(response.text)

    def _create_prompt(self, description: str) -> str:
        return f"""
        You are a diagram architecture expert. Analyze the user's natural language description and break it down into specific components, relationships, and groupings needed for a technical diagram.

        Description: {description}

        Please identify:
        1. All nodes/components mentioned (give each a unique id)
        2. Their types (e.g., ec2, rds, elb)
        3. Any grouping/clustering requirements
        4. Connections and relationships between components (using the unique ids)
        5. Any specific labeling requirements

        Respond in structured JSON format like this example:

        {{
            "nodes": [
                {{"id": "alb", "type": "elb", "label": "ALB"}},
                {{"id": "web1", "type": "ec2", "label": "Web Server 1"}},
                {{"id": "web2", "type": "ec2", "label": "Web Server 2"}},
                {{"id": "db", "type": "rds", "label": "Database"}}
            ],
            "clusters": [
                {{"id": "web_tier", "label": "Web Tier", "nodes": ["web1", "web2"]}}
            ],
            "connections": [
                {{"source": "alb", "target": "web1"}},
                {{"source": "alb", "target": "web2"}},
                {{"source": "web1", "target": "db"}},
                {{"source": "web2", "target": "db"}}
            ]
        }}
        """

    def _parse_response(self, response_text: str) -> dict:
        try:
            # The response may be wrapped in markdown, so we need to extract the JSON
            json_text = response_text.strip().replace('```json', '').replace('```', '')
            return json.loads(json_text)
        except json.JSONDecodeError:
            raise ValueError("Failed to decode LLM response as JSON.")

