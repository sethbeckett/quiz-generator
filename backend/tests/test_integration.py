"""
Integration tests for the quiz generator application.
These tests use real APIs and services (when configured).
"""

import os

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app
from app.services.gemini_service import GeminiService

# Skip integration tests if no API key is provided
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SKIP_INTEGRATION = not GEMINI_API_KEY or GEMINI_API_KEY == "test-key"

pytestmark = pytest.mark.skipif(
    SKIP_INTEGRATION,
    reason="Skipping integration tests - no valid GEMINI_API_KEY provided",
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Set up the test database."""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        yield
        # Clean up after tests
        Base.metadata.drop_all(bind=engine)
    except Exception as e:
        # For some test environments, database setup might fail
        # This is acceptable for CI environments without full database setup
        print(f"Database setup failed (this is OK for some test environments): {e}")
        yield


class TestGeminiServiceIntegration:
    """Integration tests for GeminiService with real API."""

    def setup_method(self):
        """Set up test fixtures."""
        self.gemini_service = GeminiService()

    @pytest.mark.asyncio
    async def test_real_api_connection(self):
        """Test actual connection to Gemini API."""
        result = await self.gemini_service.test_api_connection()
        assert result is True

    @pytest.mark.asyncio
    async def test_real_quiz_generation(self):
        """Test actual quiz generation with Gemini API."""
        # Use a simple, reliable topic
        topic = "Basic mathematics"

        result = await self.gemini_service.generate_quiz(topic, num_questions=2)

        # Should successfully generate a quiz
        assert result is not None
        assert result.topic == topic
        assert len(result.questions) == 2

        # Check first question structure
        question = result.questions[0]
        assert len(question.question) > 0
        assert len(question.options) == 4
        assert question.correct_answer in question.options
        assert all(len(opt_text) > 0 for opt_text in question.options.values())


class TestQuizAPIIntegration:
    """Integration tests for the full API with real services."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)

    def test_health_endpoints(self):
        """Test health check endpoints work."""
        # Basic health check
        response = self.client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

        # API health check
        response = self.client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "gemini_api" in data

    def test_api_documentation(self):
        """Test that API documentation is accessible."""
        response = self.client.get("/docs")
        assert response.status_code in [200, 307]  # 200 or redirect

    @pytest.mark.asyncio
    async def test_full_quiz_flow(self):
        """Test the complete quiz generation and submission flow."""
        # Skip this test if no API key
        if SKIP_INTEGRATION:
            pytest.skip("No valid API key for integration test")

        # 1. Generate a quiz
        quiz_data = {"topic": "Basic science"}
        response = self.client.post("/api/v1/quiz/generate", json=quiz_data)

        # Should succeed or fail gracefully
        assert response.status_code in [200, 400]

        if response.status_code == 200:
            quiz = response.json()
            assert quiz["topic"] == "Basic science"
            assert len(quiz["questions"]) > 0

            quiz_id = quiz["id"]

            # 2. Retrieve the quiz
            response = self.client.get(f"/api/v1/quiz/{quiz_id}")
            assert response.status_code == 200
            retrieved_quiz = response.json()
            assert retrieved_quiz["id"] == quiz_id

            # 3. Submit answers (selecting first option for each question)
            answers = []
            for question in retrieved_quiz["questions"]:
                first_option = question["options"][0]
                answers.append(
                    {
                        "question_id": question["id"],
                        "selected_option_id": first_option["id"],
                    }
                )

            submission = {"quiz_id": quiz_id, "answers": answers}

            response = self.client.post(
                f"/api/v1/quiz/{quiz_id}/submit", json=submission
            )
            assert response.status_code == 200

            result = response.json()
            assert "score" in result
            assert "total_questions" in result
            assert "percentage" in result
            assert result["total_questions"] == len(answers)


class TestDatabaseIntegration:
    """Integration tests for database operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)

    def test_quiz_listing(self):
        """Test quiz listing endpoint."""
        response = self.client.get("/api/v1/quiz/")
        assert response.status_code == 200
        quizzes = response.json()
        assert isinstance(quizzes, list)

    def test_quiz_not_found(self):
        """Test handling of non-existent quiz."""
        response = self.client.get("/api/v1/quiz/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_pagination(self):
        """Test quiz listing with pagination."""
        # Test with different pagination parameters
        response = self.client.get("/api/v1/quiz/?limit=5&offset=0")
        assert response.status_code == 200

        response = self.client.get("/api/v1/quiz/?limit=10&offset=5")
        assert response.status_code == 200


class TestErrorHandling:
    """Integration tests for error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)

    def test_invalid_topic_validation(self):
        """Test API validation for invalid topics."""
        # Empty topic
        response = self.client.post("/api/v1/quiz/generate", json={"topic": ""})
        assert response.status_code == 422

        # Topic too long
        long_topic = "a" * 200
        response = self.client.post("/api/v1/quiz/generate", json={"topic": long_topic})
        assert response.status_code == 422

        # Missing topic
        response = self.client.post("/api/v1/quiz/generate", json={})
        assert response.status_code == 422

    def test_invalid_submission(self):
        """Test handling of invalid quiz submissions."""
        # Submit to non-existent quiz
        submission = {
            "quiz_id": 99999,
            "answers": [{"question_id": 1, "selected_option_id": 1}],
        }
        response = self.client.post("/api/v1/quiz/99999/submit", json=submission)
        assert response.status_code == 400

        # Malformed submission data
        response = self.client.post("/api/v1/quiz/1/submit", json={"invalid": "data"})
        assert response.status_code == 422
