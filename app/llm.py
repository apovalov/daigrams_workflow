from __future__ import annotations

from google import genai

from app.config import settings

__all__ = ["client"]

# Configure the GenAI client with fallback to Vertex AI
if settings.use_vertex_ai and settings.google_cloud_project:
    client = genai.Client(
        vertexai=True,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location,
    )
else:
    client = genai.Client(api_key=settings.gemini_api_key)
