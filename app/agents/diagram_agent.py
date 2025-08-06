import json
import os

import google.generativeai as genai


class DiagramAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    async def generate_analysis(self, description: str) -> dict:
        prompt = self._create_prompt(description)
        response = await self.model.generate_content_async(prompt)
        return self._parse_response(response.text)

    def _create_prompt(self, description: str) -> str:
        return f"""
        You are a diagram architecture expert. Analyze the user's natural language description and break it down into specific components, relationships, and groupings needed for a technical diagram.

        Description: {description}

        Available component types:
        - Compute: ec2, lambda, service, microservice, web_server
        - Database: rds, dynamodb, database
        - Network & Load Balancing: elb, alb, nlb, api_gateway, apigateway, gateway
        - Storage: s3
        - Integration & Messaging: sqs, sns, queue
        - Management & Monitoring: cloudwatch, monitoring
        - Security: iam, cognito, auth_service
        - Analytics: kinesis
        - Developer Tools: codebuild, codepipeline

        Please identify:
        1. All nodes/components mentioned (give each a unique id)
        2. Their types (use the available types listed above)
        3. Any grouping/clustering requirements
        4. Connections and relationships between components (using the unique ids)
        5. Any specific labeling requirements

        For microservices, use "service" or "microservice" type, or specific service types like "auth_service", "payment_service", "order_service".
        For Application Load Balancer, use "alb" type.
        For API Gateway, use "api_gateway" type.
        For SQS queues, use "sqs" type.
        For CloudWatch monitoring, use "cloudwatch" type.

        Respond in structured JSON format like this example:

        {{
            "nodes": [
                {{"id": "alb", "type": "alb", "label": "Application Load Balancer"}},
                {{"id": "web1", "type": "ec2", "label": "Web Server 1"}},
                {{"id": "web2", "type": "ec2", "label": "Web Server 2"}},
                {{"id": "db", "type": "rds", "label": "Database"}},
                {{"id": "api_gw", "type": "api_gateway", "label": "API Gateway"}},
                {{"id": "auth_svc", "type": "auth_service", "label": "Authentication Service"}},
                {{"id": "queue", "type": "sqs", "label": "Message Queue"}},
                {{"id": "monitoring", "type": "cloudwatch", "label": "CloudWatch"}}
            ],
            "clusters": [
                {{"id": "web_tier", "label": "Web Tier", "nodes": ["web1", "web2"]}},
                {{"id": "microservices", "label": "Microservices", "nodes": ["auth_svc"]}}
            ],
            "connections": [
                {{"source": "alb", "target": "web1"}},
                {{"source": "alb", "target": "web2"}},
                {{"source": "web1", "target": "db"}},
                {{"source": "web2", "target": "db"}},
                {{"source": "api_gw", "target": "auth_svc"}},
                {{"source": "auth_svc", "target": "queue"}}
            ]
        }}
        """

    def _parse_response(self, response_text: str) -> dict:
        try:
            # The response may be wrapped in markdown, so we need to extract the JSON
            json_text = response_text.strip().replace("```json", "").replace("```", "")
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError("Failed to decode LLM response as JSON.") from e
