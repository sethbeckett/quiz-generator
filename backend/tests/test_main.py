"""
Tests for main FastAPI application.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestMainApp:
    """Test suite for main application."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"

    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data

    @patch("app.services.gemini_service.gemini_service")
    def test_api_health_check(self, mock_gemini_service):
        """Test API health check with Gemini status."""
        # Mock Gemini service
        mock_gemini_service.test_api_connection = AsyncMock(return_value=True)

        response = self.client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["gemini_api"] == "connected"

    def test_docs_available_in_debug(self):
        """Test that docs are available in debug mode."""
        response = self.client.get("/docs")
        # Should not return 404 if docs are enabled
        assert response.status_code in [200, 307]  # 307 for redirect
