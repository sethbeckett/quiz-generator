"""
Tests for Gemini service with edge cases and error handling.
"""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.config import settings
from app.schemas.quiz import GeminiQuizResponse, GeneratedQuizQuestion
from app.services.gemini_service import GeminiService


class TestGeminiService:
    """Test suite for GeminiService."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("app.services.gemini_service.settings") as mock_settings:
            mock_settings.gemini_api_key = "test-key"
            mock_settings.gemini_model = "gemini-2.5-flash"
            mock_settings.gemini_thinking_budget = 1024
            mock_settings.default_options_per_question = 4
            self.gemini_service = GeminiService()

    def test_validate_topic_valid(self):
        """Test topic validation with valid topics."""
        assert self.gemini_service.validate_topic("Python Programming") == True
        assert self.gemini_service.validate_topic("History of Rome") == True
        assert self.gemini_service.validate_topic("Machine Learning") == True

    def test_validate_topic_invalid(self):
        """Test topic validation with invalid topics."""
        assert self.gemini_service.validate_topic("") == False
        assert self.gemini_service.validate_topic("   ") == False
        assert self.gemini_service.validate_topic("a" * 101) == False  # Too long
        assert self.gemini_service.validate_topic("explicit content") == False
        assert self.gemini_service.validate_topic("NSFW material") == False

    def test_validate_quiz_business_rules_valid(self):
        """Test business rules validation with valid quiz."""
        quiz_response = GeminiQuizResponse(
            topic="Test Topic",
            questions=[
                GeneratedQuizQuestion(
                    question="What is 2+2?",
                    options={"A": "3", "B": "4", "C": "5", "D": "6"},
                    correct_answer="B",
                    explanation="Basic math",
                ),
                GeneratedQuizQuestion(
                    question="What is 3+3?",
                    options={"A": "5", "B": "6", "C": "7", "D": "8"},
                    correct_answer="B",
                    explanation="Basic math",
                ),
            ],
        )

        assert (
            self.gemini_service._validate_quiz_business_rules(quiz_response, 2) == True
        )

    def test_validate_quiz_business_rules_wrong_question_count(self):
        """Test business rules validation with wrong number of questions."""
        quiz_response = GeminiQuizResponse(
            topic="Test Topic",
            questions=[
                GeneratedQuizQuestion(
                    question="What is 2+2?",
                    options={"A": "3", "B": "4", "C": "5", "D": "6"},
                    correct_answer="B",
                )
            ],
        )

        assert (
            self.gemini_service._validate_quiz_business_rules(quiz_response, 5) == False
        )

    def test_validate_quiz_business_rules_empty_question(self):
        """Test business rules validation with empty question text."""
        quiz_response = GeminiQuizResponse(
            topic="Test Topic",
            questions=[
                GeneratedQuizQuestion(
                    question="",  # Empty question
                    options={"A": "3", "B": "4", "C": "5", "D": "6"},
                    correct_answer="B",
                )
            ],
        )

        assert (
            self.gemini_service._validate_quiz_business_rules(quiz_response, 1) == False
        )

    def test_validate_quiz_business_rules_wrong_option_count(self):
        """Test business rules validation with wrong number of options."""
        quiz_response = GeminiQuizResponse(
            topic="Test Topic",
            questions=[
                GeneratedQuizQuestion(
                    question="What is 2+2?",
                    options={"A": "3", "B": "4"},  # Only 2 options
                    correct_answer="B",
                )
            ],
        )

        assert (
            self.gemini_service._validate_quiz_business_rules(quiz_response, 1) == False
        )

    def test_validate_quiz_business_rules_wrong_option_letters(self):
        """Test business rules validation with incorrect option letters."""
        quiz_response = GeminiQuizResponse(
            topic="Test Topic",
            questions=[
                GeneratedQuizQuestion(
                    question="What is 2+2?",
                    options={"X": "3", "Y": "4", "Z": "5", "W": "6"},  # Wrong letters
                    correct_answer="Y",
                )
            ],
        )

        assert (
            self.gemini_service._validate_quiz_business_rules(quiz_response, 1) == False
        )

    def test_validate_quiz_business_rules_invalid_correct_answer(self):
        """Test business rules validation with invalid correct answer."""
        quiz_response = GeminiQuizResponse(
            topic="Test Topic",
            questions=[
                GeneratedQuizQuestion(
                    question="What is 2+2?",
                    options={"A": "3", "B": "4", "C": "5", "D": "6"},
                    correct_answer="E",  # Not in options
                )
            ],
        )

        assert (
            self.gemini_service._validate_quiz_business_rules(quiz_response, 1) == False
        )

    def test_validate_quiz_business_rules_empty_option_text(self):
        """Test business rules validation with empty option text."""
        quiz_response = GeminiQuizResponse(
            topic="Test Topic",
            questions=[
                GeneratedQuizQuestion(
                    question="What is 2+2?",
                    options={"A": "", "B": "4", "C": "5", "D": "6"},  # Empty option A
                    correct_answer="B",
                )
            ],
        )

        assert (
            self.gemini_service._validate_quiz_business_rules(quiz_response, 1) == False
        )

    @pytest.mark.asyncio
    async def test_generate_quiz_malformed_json(self):
        """Test quiz generation with malformed JSON response."""
        with patch("google.generativeai.GenerativeModel") as mock_model_class:
            mock_model = AsyncMock()
            mock_response = Mock()
            mock_response.text = "Invalid JSON {{"
            mock_model.generate_content_async.return_value = mock_response
            mock_model_class.return_value = mock_model

            result = await self.gemini_service.generate_quiz("Test Topic")
            assert result is None

    @pytest.mark.asyncio
    async def test_generate_quiz_empty_response(self):
        """Test quiz generation with empty response."""
        with patch("google.generativeai.GenerativeModel") as mock_model_class:
            mock_model = AsyncMock()
            mock_response = Mock()
            mock_response.text = ""
            mock_model.generate_content_async.return_value = mock_response
            mock_model_class.return_value = mock_model

            result = await self.gemini_service.generate_quiz("Test Topic")
            assert result is None

    @pytest.mark.asyncio
    async def test_generate_quiz_invalid_schema(self):
        """Test quiz generation with response that doesn't match schema."""
        with patch("google.generativeai.GenerativeModel") as mock_model_class:
            mock_model = AsyncMock()
            mock_response = Mock()
            mock_response.text = json.dumps(
                {
                    "topic": "Test",
                    "invalid_field": "invalid_value",  # Missing questions field
                }
            )
            mock_model.generate_content_async.return_value = mock_response
            mock_model_class.return_value = mock_model

            result = await self.gemini_service.generate_quiz("Test Topic")
            assert result is None

    @pytest.mark.asyncio
    async def test_generate_quiz_api_exception(self):
        """Test quiz generation when API throws exception."""
        with patch("google.generativeai.GenerativeModel") as mock_model_class:
            mock_model = AsyncMock()
            mock_model.generate_content_async.side_effect = Exception("API Error")
            mock_model_class.return_value = mock_model

            result = await self.gemini_service.generate_quiz("Test Topic")
            assert result is None

    @pytest.mark.asyncio
    async def test_test_api_connection_success(self):
        """Test successful API connection test."""
        with patch("google.generativeai.GenerativeModel") as mock_model_class:
            mock_model = AsyncMock()
            mock_response = Mock()
            mock_response.text = "API connection successful"
            mock_model.generate_content_async.return_value = mock_response
            mock_model_class.return_value = mock_model

            result = await self.gemini_service.test_api_connection()
            assert result == True

    @pytest.mark.asyncio
    async def test_test_api_connection_failure(self):
        """Test failed API connection test."""
        with patch("google.generativeai.GenerativeModel") as mock_model_class:
            mock_model = AsyncMock()
            mock_model.generate_content_async.side_effect = Exception(
                "Connection failed"
            )
            mock_model_class.return_value = mock_model

            result = await self.gemini_service.test_api_connection()
            assert result == False
