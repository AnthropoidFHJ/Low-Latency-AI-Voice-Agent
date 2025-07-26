import pytest
import asyncio
from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))
from app.main import app
from app.voice_agent import voice_agent
from app.config import settings
class TestBasicSetup:
    def test_app_creation(self):
        assert app is not None
        assert app.title == "Ultra-Low Latency Voice Agent"
    def test_settings_loaded(self):
        assert settings is not None
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
    def test_voice_agent_initialization(self):
        assert voice_agent is not None
        assert voice_agent.form_manager is not None
class TestHealthEndpoint:
    def setup_method(self):
        self.client = TestClient(app)
    def test_health_endpoint(self):
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "performance_metrics" in data
class TestFormManager:
    @pytest.mark.asyncio
    async def test_form_manager_initialization(self):
        from app.tools.form_manager import FormManager
        form_manager = FormManager()
        assert form_manager is not None
        assert len(form_manager.form_templates) > 0
        assert "contact" in form_manager.form_templates
    @pytest.mark.asyncio
    async def test_open_contact_form(self):
        from app.tools.form_manager import FormManager
        form_manager = FormManager()
        result = await form_manager.open_form("contact", "Test Contact Form")
        assert result["success"] is True
        assert result["form_type"] == "contact"
        assert result["title"] == "Test Contact Form"
        assert len(result["fields"]) > 0
    @pytest.mark.asyncio
    async def test_fill_form_field(self):
        from app.tools.form_manager import FormManager
        form_manager = FormManager()
        await form_manager.open_form("contact")
        result = await form_manager.fill_field("name", "John Doe")
        assert result["success"] is True
        assert result["field_name"] == "name"
        assert result["value"] == "John Doe"
class TestVoiceAgent:
    @pytest.mark.asyncio
    async def test_voice_agent_initialization(self):
        try:
            result = await voice_agent.initialize()
            if os.getenv("GOOGLE_API_KEY"):
                assert result is True
            else:
                assert result is False
        except Exception as e:
            assert "GOOGLE_API_KEY" in str(e) or "API" in str(e)
    @pytest.mark.asyncio
    async def test_handle_function_call(self):
        result = await voice_agent.handle_function_call("open_form", {
            "form_type": "contact",
            "title": "Test Form"
        })
        assert "success" in result
    def test_get_metrics(self):
        metrics = voice_agent.get_metrics()
        assert "total_requests" in metrics
        assert "active_connections" in metrics
        assert "timestamp" in metrics
        assert "is_initialized" in metrics
class TestWebSocketConnection:
    def setup_method(self):
        self.client = TestClient(app)
    def test_websocket_endpoint_exists(self):
        websocket_routes = [route for route in app.routes if hasattr(route, 'path') and '/ws/voice' in route.path]
        assert len(websocket_routes) > 0
if __name__ == "__main__":
    pytest.main([__file__, "-v"])