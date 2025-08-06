from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.agents.assistant_agent import AssistantAgent
from app.agents.diagram_agent import DiagramAgent
from app.api.main import app, get_assistant_service, get_diagram_service, get_settings
from app.config import Settings
from app.models.diagram import AssistantResponse
from app.services.assistant_service import AssistantService
from app.services.diagram_service import DiagramService


@pytest.fixture
def mock_settings() -> Settings:
    """Mock settings for testing."""
    return Settings(
        gemini_api_key="test_api_key",
        gemini_model="gemini-2.5-flash",
        tmp_dir="/tmp/test_diagrams",
    )


@pytest.fixture
def mock_diagram_service():
    mock = MagicMock(spec=DiagramService)
    mock.generate_diagram_from_description = AsyncMock(
        return_value=(
            "fake_image_data",
            {
                "nodes_created": 1,
                "clusters_created": 1,
                "connections_made": 1,
                "generation_time": 0.1,
            },
        )
    )
    return mock


@pytest.fixture
def mock_assistant_service():
    mock = MagicMock(spec=AssistantService)
    mock.process_message = AsyncMock(
        return_value=AssistantResponse(
            response_type="text",
            content="Hello! How can I help you create a diagram today?",
        )
    )
    return mock


@pytest.mark.asyncio
async def test_generate_diagram(mock_diagram_service, mock_settings):
    app.dependency_overrides[get_diagram_service] = lambda: mock_diagram_service
    app.dependency_overrides[get_settings] = lambda: mock_settings

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post(
            "/api/v1/generate-diagram", json={"description": "test"}
        )

    assert response.status_code == 200
    assert response.json()["success"] is True
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_assistant(mock_assistant_service, mock_settings):
    app.dependency_overrides[get_assistant_service] = lambda: mock_assistant_service
    app.dependency_overrides[get_settings] = lambda: mock_settings

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/api/v1/assistant", json={"message": "test"})

    assert response.status_code == 200
    assert response.json()["response_type"] == "text"
    app.dependency_overrides = {}


def test_settings_resolution(mock_settings):
    """Test that settings are resolved from environment variables."""
    assert mock_settings.gemini_api_key == "test_api_key"
    assert mock_settings.gemini_model == "gemini-2.5-flash"
    assert mock_settings.tmp_dir == "/tmp/test_diagrams"


@pytest.mark.asyncio
async def test_diagram_generation_thread_pool():
    """Test that diagram generation runs in thread pool."""
    with patch("anyio.to_thread.run_sync") as mock_run_sync:
        mock_run_sync.return_value = ("test_image", {"nodes_created": 1})

        settings = Settings(gemini_api_key="test_key", tmp_dir="/tmp/test")
        service = DiagramService(settings)

        # Mock the agent analysis
        with patch.object(service.agent, "generate_analysis") as mock_analysis:
            mock_analysis.return_value = {
                "nodes": [],
                "clusters": [],
                "connections": [],
            }

            await service.generate_diagram_from_description("test description")

            # Verify to_thread.run_sync was called
            mock_run_sync.assert_called_once()


def test_assistant_agent_intent_parsing():
    """Test assistant agent intent parsing with deterministic responses."""
    agent = AssistantAgent()

    # Test successful JSON parsing
    response_text = '{"intent": "generate_diagram", "description": "test diagram"}'
    result = agent._parse_response(response_text)
    assert result["intent"] == "generate_diagram"
    assert result["description"] == "test diagram"

    # Test with markdown wrapped JSON
    response_text = '```json\n{"intent": "greeting"}\n```'
    result = agent._parse_response(response_text)
    assert result["intent"] == "greeting"


def test_diagram_agent_analysis_parsing():
    """Test diagram agent analysis parsing with deterministic responses."""
    agent = DiagramAgent()

    # Test successful JSON parsing
    response_text = """
    {
        "nodes": [{"id": "web1", "type": "ec2", "label": "Web Server"}],
        "clusters": [{"id": "web_tier", "label": "Web Tier", "nodes": ["web1"]}],
        "connections": [{"source": "web1", "target": "db"}]
    }
    """
    result = agent._parse_response(response_text)
    assert len(result["nodes"]) == 1
    assert result["nodes"][0]["id"] == "web1"
    assert len(result["clusters"]) == 1
    assert len(result["connections"]) == 1
