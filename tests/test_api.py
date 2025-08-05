import pytest
from httpx import AsyncClient, ASGITransport
from app.api.main import app, get_diagram_service, get_assistant_service
from app.services.diagram_service import DiagramService
from app.services.assistant_service import AssistantService
from app.models.diagram import AssistantResponse
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def mock_diagram_service():
    mock = MagicMock(spec=DiagramService)
    mock.generate_diagram_from_description = AsyncMock(return_value=("fake_image_data", {
        "nodes_created": 1,
        "clusters_created": 1,
        "connections_made": 1,
        "generation_time": 0.1
    }))
    return mock

@pytest.fixture
def mock_assistant_service():
    mock = MagicMock(spec=AssistantService)
    mock.process_message = AsyncMock(return_value=AssistantResponse(
        response_type="text",
        content="Hello! How can I help you create a diagram today?"
    ))
    return mock

@pytest.mark.asyncio
async def test_generate_diagram(mock_diagram_service):
    app.dependency_overrides[get_diagram_service] = lambda: mock_diagram_service
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/generate-diagram", json={"description": "test"})
    assert response.status_code == 200
    assert response.json()["success"] == True
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_assistant(mock_assistant_service):
    app.dependency_overrides[get_assistant_service] = lambda: mock_assistant_service
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/assistant", json={"message": "test"})
    assert response.status_code == 200
    assert response.json()["response_type"] == "text"
    app.dependency_overrides = {}