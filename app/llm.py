from __future__ import annotations

import google.generativeai as genai
from google.generativeai import GenerativeModel

from app.config import settings

__all__ = ["model"]

# Configure the Gemini API once globally
genai.configure(api_key=settings.gemini_api_key)

# Shared model instance
model = GenerativeModel(settings.gemini_model)
