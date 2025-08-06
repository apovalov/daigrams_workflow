# Diagram API Service

This project is an async Python API service that generates diagrams from natural language descriptions using LLM agents and the `diagrams` package.

## Setup

### Local Development

1.  **Install Python 3.11+**
2.  **Install uv:** `pip install uv`
3.  **Create a virtual environment:** `uv venv`
4.  **Activate the virtual environment:** `source .venv/bin/activate`
5.  **Install dependencies:** `uv pip install -e .`
6.  **Create a `.env` file with your Gemini API key:**
    ```bash
    cp .env.example .env
    # Edit .env and add your actual Gemini API key
    ```
7.  **Run the application:** `uvicorn app.api.main:app --reload`

### Docker

1.  **Build the image:** `docker-compose build`
2.  **Run the container:** `docker-compose up`

## API Usage

### Generate Diagram

*   **POST** `/api/v1/generate-diagram`

**Request Body:**

```json
{
  "description": "Create a diagram showing a basic web application with an Application Load Balancer, two EC2 instances for the web servers, and an RDS database for storage. The web servers should be in a cluster named 'Web Tier'"
}
```

### Assistant

*   **POST** `/api/v1/assistant`

**Request Body:**

```json
{
  "message": "I want to create a diagram for a serverless application"
}
```
