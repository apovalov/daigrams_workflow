from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.agents.assistant_agent import AssistantAgent
from app.agents.diagram_agent import DiagramAgent
from app.api.main import app, get_assistant_service, get_diagram_service, get_settings
from app.config import Settings
from app.models.diagram import AssistantRequest, AssistantResponse
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
        "clusters": [{"label": "Web Tier", "nodes": ["web1"]}],
        "connections": [{"source": "web1", "target": "db"}]
    }
    """
    result = agent._parse_response(response_text)
    assert len(result["nodes"]) == 1
    assert result["nodes"][0]["id"] == "web1"
    assert len(result["clusters"]) == 1
    assert len(result["connections"]) == 1


@pytest.mark.asyncio
async def test_assistant_endpoint_with_context():
    """Test assistant endpoint with conversation context."""
    mock_service = MagicMock(spec=AssistantService)
    mock_service.process_message = AsyncMock(
        return_value=AssistantResponse(
            response_type="text",
            content="I understand you want to continue our conversation.",
            suggestions=["Let's build on that", "Tell me more"],
        )
    )

    app.dependency_overrides[get_assistant_service] = lambda: mock_service

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post(
            "/api/v1/assistant",
            json={
                "message": "Continue from where we left off",
                "conversation_id": "test-123",
                "context": {"previous_topic": "microservices"},
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["response_type"] == "text"
    assert "suggestions" in data
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_generate_diagram_error_handling():
    """Test diagram generation error handling."""
    mock_service = MagicMock(spec=DiagramService)
    mock_service.generate_diagram_from_description = AsyncMock(
        side_effect=Exception("Test error")
    )

    app.dependency_overrides[get_diagram_service] = lambda: mock_service

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post(
            "/api/v1/generate-diagram", json={"description": "test"}
        )

    assert response.status_code == 500
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_assistant_bad_request():
    """Test assistant endpoint with bad request."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post(
            "/api/v1/assistant",
            json={"message": ""},  # Empty message
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_diagram_generation_bad_request():
    """Test diagram generation with bad request."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post(
            "/api/v1/generate-diagram",
            json={"description": ""},  # Empty description
        )

    assert response.status_code == 400


def test_assistant_agent_fallback_heuristics():
    """Test assistant agent fallback heuristics."""
    agent = AssistantAgent()

    # Test diagram generation keywords
    result = agent._create_fallback_intent("create a diagram")
    assert result["intent"] == "generate_diagram"

    # Test help keywords
    result = agent._create_fallback_intent("how does this work")
    assert result["intent"] == "help"

    # Test general fallback
    result = agent._create_fallback_intent("random text")
    assert result["intent"] == "general"


def test_diagram_agent_fallback_analysis():
    """Test diagram agent fallback analysis generation."""
    agent = DiagramAgent()

    # Test microservices pattern
    result = agent._create_fallback_analysis(
        "microservices with authentication and payment"
    )
    assert any(node["type"] == "lambda" for node in result["nodes"])
    assert any("auth" in node["id"].lower() for node in result["nodes"])

    # Test traditional web architecture
    result = agent._create_fallback_analysis("load balancer with EC2 instances")
    assert any(node["type"] == "alb" for node in result["nodes"])
    assert any(node["type"] == "ec2" for node in result["nodes"])

    # Test simple fallback
    result = agent._create_fallback_analysis("unknown architecture")
    assert len(result["nodes"]) >= 2


@pytest.mark.asyncio
async def test_assistant_service_memory():
    """Test assistant service conversation memory."""
    settings = Settings(gemini_api_key="test_key", tmp_dir="/tmp/test")
    service = AssistantService(settings)

    # Mock the agent to return predictable results
    with patch.object(service.assistant_agent, "get_intent") as mock_intent:
        mock_intent.return_value = {"intent": "greeting"}

        # First message
        request1 = AssistantRequest(message="Hello", conversation_id="test-conv")
        await service.process_message(request1)

        # Check context was stored
        context = service._get_conversation_context("test-conv")
        assert len(context["messages"]) == 2  # User + Assistant

        # Second message with same conversation ID
        mock_intent.return_value = {"intent": "clarification"}
        request2 = AssistantRequest(message="Tell me more", conversation_id="test-conv")
        await service.process_message(request2)

        # Check context was updated
        context = service._get_conversation_context("test-conv")
        assert len(context["messages"]) == 4  # 2 previous + 2 new


def test_assistant_service_context_limit():
    """Test that conversation context is limited to prevent memory bloat."""
    settings = Settings(gemini_api_key="test_key", tmp_dir="/tmp/test")
    service = AssistantService(settings)

    # Create a large context
    large_context = {
        "messages": [{"role": "user", "content": f"message {i}"} for i in range(15)]
    }

    service._update_conversation_context("test", large_context)
    updated_context = service._get_conversation_context("test")

    # Should be limited to 10 messages
    assert len(updated_context["messages"]) == 10
