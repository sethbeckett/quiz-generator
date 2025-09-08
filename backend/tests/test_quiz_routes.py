"""
Tests for quiz API routes with edge cases and error handling.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.quiz import Question, QuestionOption, Quiz
from app.schemas.quiz import (
    FeedbackQuestion,
    FeedbackRequest,
    GeminiQuizResponse,
    GeneratedQuizQuestion,
)

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


class TestQuizRoutes:
    """Test suite for quiz API routes."""

    def setup_method(self):
        """Set up test fixtures."""
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def teardown_method(self):
        """Clean up after tests."""
        Base.metadata.drop_all(bind=engine)

    @patch("app.services.quiz_service.gemini_service")
    def test_generate_quiz_success(self, mock_gemini_service):
        """Test successful quiz generation."""
        # Mock successful Gemini response
        mock_gemini_service.validate_topic.return_value = True
        mock_gemini_service.generate_quiz = AsyncMock(
            return_value=GeminiQuizResponse(
                topic="Python Programming",
                questions=[
                    GeneratedQuizQuestion(
                        question="What is Python?",
                        options={
                            "A": "Snake",
                            "B": "Programming Language",
                            "C": "Tool",
                            "D": "Framework",
                        },
                        correct_answer="B",
                        explanation="Python is a programming language",
                    )
                ],
            )
        )

        response = self.client.post(
            "/api/v1/quiz/generate", json={"topic": "Python Programming"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["topic"] == "Python Programming"
        assert len(data["questions"]) == 1
        assert data["questions"][0]["question_text"] == "What is Python?"

    @patch("app.services.quiz_service.gemini_service")
    def test_generate_quiz_invalid_topic(self, mock_gemini_service):
        """Test quiz generation with invalid topic."""
        mock_gemini_service.validate_topic.return_value = False

        response = self.client.post("/api/v1/quiz/generate", json={"topic": ""})

        assert response.status_code == 422  # Validation error for empty topic
        assert "field required" in str(
            response.json()
        ) or "String should have at least 1 character" in str(response.json())

    @patch("app.services.quiz_service.gemini_service")
    def test_generate_quiz_gemini_failure(self, mock_gemini_service):
        """Test quiz generation when Gemini API fails."""
        mock_gemini_service.validate_topic.return_value = True
        mock_gemini_service.generate_quiz = AsyncMock(
            return_value=None
        )  # Simulate failure

        response = self.client.post(
            "/api/v1/quiz/generate", json={"topic": "Valid Topic"}
        )

        assert response.status_code == 400
        assert "Failed to generate quiz" in response.json()["detail"]

    def test_generate_quiz_missing_topic(self):
        """Test quiz generation with missing topic field."""
        response = self.client.post("/api/v1/quiz/generate", json={})

        assert response.status_code == 422  # Validation error

    def test_generate_quiz_topic_too_long(self):
        """Test quiz generation with topic that's too long."""
        long_topic = "a" * 101  # Max is 100 characters

        response = self.client.post("/api/v1/quiz/generate", json={"topic": long_topic})

        assert response.status_code == 422  # Validation error

    def test_get_quiz_not_found(self):
        """Test getting a quiz that doesn't exist."""
        response = self.client.get("/api/v1/quiz/999")

        assert response.status_code == 404
        assert "Quiz with ID 999 not found" in response.json()["detail"]

    def test_submit_quiz_not_found(self):
        """Test submitting answers for non-existent quiz."""
        response = self.client.post(
            "/api/v1/quiz/999/submit",
            json={
                "quiz_id": 999,
                "answers": [{"question_id": 1, "selected_option_id": 1}],
            },
        )

        assert response.status_code == 400
        assert "Failed to process quiz submission" in response.json()["detail"]

    def test_submit_quiz_id_mismatch(self):
        """Test submitting with mismatched quiz IDs."""
        response = self.client.post(
            "/api/v1/quiz/1/submit",
            json={
                "quiz_id": 2,  # Different from URL
                "answers": [{"question_id": 1, "selected_option_id": 1}],
            },
        )

        assert response.status_code == 400
        assert "Quiz ID in URL does not match" in response.json()["detail"]

    def test_submit_quiz_malformed_data(self):
        """Test submitting quiz with malformed answer data."""
        response = self.client.post(
            "/api/v1/quiz/1/submit",
            json={"quiz_id": 1, "answers": [{"invalid_field": "invalid_value"}]},
        )

        assert response.status_code == 422  # Validation error

    def test_get_quiz_attempts_not_found(self):
        """Test getting attempts for non-existent quiz."""
        response = self.client.get("/api/v1/quiz/999/attempts")

        assert response.status_code == 404
        assert "Quiz with ID 999 not found" in response.json()["detail"]

    def test_list_quizzes_pagination(self):
        """Test quiz listing with pagination parameters."""
        response = self.client.get("/api/v1/quiz/?limit=5&offset=10")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_quizzes_invalid_pagination(self):
        """Test quiz listing with invalid pagination parameters."""
        response = self.client.get("/api/v1/quiz/?limit=-1&offset=-1")

        # Should still work but with default values
        assert response.status_code == 200

    @patch("app.services.quiz_service.gemini_service")
    def test_feedback_endpoint(self, mock_gemini_service):
        """Test feedback generation for incorrect answers."""
        # Prepare a quiz in DB
        db = TestingSessionLocal()
        quiz = Quiz(topic="Topic")
        q = Question(question_text="Q?", question_order=1, quiz=quiz)
        _opta = QuestionOption(
            option_text="A1", option_letter="A", is_correct=True, question=q
        )
        _optb = QuestionOption(
            option_text="B1", option_letter="B", is_correct=False, question=q
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        db.close()

        # Mock gemini feedback
        mock_gemini_service.explain_incorrect_answers = AsyncMock(
            return_value={"items": [{"question_id": 1, "explanation": "Because ..."}]}
        )

        payload = {
            "topic": "Topic",
            "items": [
                {
                    "question_id": 1,
                    "question_text": "Q?",
                    "user_selected": "B",
                    "user_selected_text": "B1",
                    "correct_option": "A",
                    "correct_text": "A1",
                }
            ],
        }

        response = self.client.post(f"/api/v1/quiz/{quiz.id}/feedback", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestQuizRoutesEndToEnd:
    """End-to-end tests for quiz routes with real database operations."""

    def setup_method(self):
        """Set up test database and client."""
        # Create a fresh test database for each test
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def teardown_method(self):
        """Clean up test database."""
        Base.metadata.drop_all(bind=engine)

    def test_full_quiz_flow_success(self):
        """Test the complete quiz flow: generate -> retrieve -> submit."""
        # Step 1: Mock Gemini service and generate a quiz
        with patch("app.services.gemini_service.gemini_service") as mock_gemini:
            mock_gemini.validate_topic.return_value = True
            mock_gemini.generate_quiz = AsyncMock(
                return_value=GeminiQuizResponse(
                    topic="Mathematics",
                    questions=[
                        GeneratedQuizQuestion(
                            question="What is 2+2?",
                            options={"A": "3", "B": "4", "C": "5", "D": "6"},
                            correct_answer="B",
                            explanation="Basic addition: 2+2=4",
                        ),
                        GeneratedQuizQuestion(
                            question="What is 3*3?",
                            options={"A": "6", "B": "8", "C": "9", "D": "12"},
                            correct_answer="C",
                            explanation="Basic multiplication: 3*3=9",
                        ),
                    ],
                )
            )

            # Generate quiz
            response = self.client.post(
                "/api/v1/quiz/generate", json={"topic": "Mathematics"}
            )

            assert response.status_code == 200
            quiz_data = response.json()
            quiz_id = quiz_data["id"]
            assert quiz_data["topic"] == "Mathematics"
            assert len(quiz_data["questions"]) == 2

        # Step 2: Retrieve the quiz
        response = self.client.get(f"/api/v1/quiz/{quiz_id}")
        assert response.status_code == 200
        retrieved_quiz = response.json()
        assert retrieved_quiz["id"] == quiz_id
        assert len(retrieved_quiz["questions"]) == 2

        # Step 3: Submit answers (all correct)
        questions = retrieved_quiz["questions"]

        # Find correct answers
        correct_answers = []
        for question in questions:
            correct_option = next(
                opt for opt in question["options"] if opt["is_correct"]
            )
            correct_answers.append(
                {
                    "question_id": question["id"],
                    "selected_option_id": correct_option["id"],
                }
            )

        submission = {"quiz_id": quiz_id, "answers": correct_answers}

        response = self.client.post(f"/api/v1/quiz/{quiz_id}/submit", json=submission)
        assert response.status_code == 200

        result = response.json()
        assert result["score"] == 2
        assert result["total_questions"] == 2
        assert result["percentage"] == 100.0
        assert len(result["correct_answers"]) == 2

        # Verify all answers were marked correct
        for answer in result["correct_answers"]:
            assert answer["is_correct"] is True

    def test_full_quiz_flow_partial_correct(self):
        """Test quiz flow with some correct and some incorrect answers."""
        # Generate quiz (same as above)
        with patch("app.services.gemini_service.gemini_service") as mock_gemini:
            mock_gemini.validate_topic.return_value = True
            mock_gemini.generate_quiz = AsyncMock(
                return_value=GeminiQuizResponse(
                    topic="Mathematics",
                    questions=[
                        GeneratedQuizQuestion(
                            question="What is 2+2?",
                            options={"A": "3", "B": "4", "C": "5", "D": "6"},
                            correct_answer="B",
                        ),
                        GeneratedQuizQuestion(
                            question="What is 3*3?",
                            options={"A": "6", "B": "8", "C": "9", "D": "12"},
                            correct_answer="C",
                        ),
                    ],
                )
            )

            response = self.client.post(
                "/api/v1/quiz/generate", json={"topic": "Mathematics"}
            )

            quiz_data = response.json()
            quiz_id = quiz_data["id"]

        # Get quiz details
        response = self.client.get(f"/api/v1/quiz/{quiz_id}")
        retrieved_quiz = response.json()
        questions = retrieved_quiz["questions"]

        # Submit answers - one correct, one incorrect
        answers = []
        for i, question in enumerate(questions):
            if i == 0:
                # First question: select correct answer
                correct_option = next(
                    opt for opt in question["options"] if opt["is_correct"]
                )
                answers.append(
                    {
                        "question_id": question["id"],
                        "selected_option_id": correct_option["id"],
                    }
                )
            else:
                # Second question: select incorrect answer
                incorrect_option = next(
                    opt for opt in question["options"] if not opt["is_correct"]
                )
                answers.append(
                    {
                        "question_id": question["id"],
                        "selected_option_id": incorrect_option["id"],
                    }
                )

        submission = {"quiz_id": quiz_id, "answers": answers}

        response = self.client.post(f"/api/v1/quiz/{quiz_id}/submit", json=submission)
        assert response.status_code == 200

        result = response.json()
        assert result["score"] == 1  # Only one correct
        assert result["total_questions"] == 2
        assert result["percentage"] == 50.0
        assert len(result["correct_answers"]) == 2

        # Verify answer correctness
        answer_results = result["correct_answers"]
        correct_count = sum(1 for a in answer_results if a["is_correct"])
        assert correct_count == 1

    def test_quiz_attempts_tracking(self):
        """Test that quiz attempts are properly tracked."""
        # Generate a quiz
        with patch("app.services.gemini_service.gemini_service") as mock_gemini:
            mock_gemini.validate_topic.return_value = True
            mock_gemini.generate_quiz = AsyncMock(
                return_value=GeminiQuizResponse(
                    topic="Test",
                    questions=[
                        GeneratedQuizQuestion(
                            question="Test question?",
                            options={
                                "A": "Answer A",
                                "B": "Answer B",
                                "C": "Answer C",
                                "D": "Answer D",
                            },
                            correct_answer="A",
                        )
                    ],
                )
            )

            response = self.client.post("/api/v1/quiz/generate", json={"topic": "Test"})

            quiz_id = response.json()["id"]

        # Submit the quiz twice with different answers
        response = self.client.get(f"/api/v1/quiz/{quiz_id}")
        quiz_data = response.json()
        question = quiz_data["questions"][0]

        # First attempt - correct answer
        correct_option = next(opt for opt in question["options"] if opt["is_correct"])
        submission1 = {
            "quiz_id": quiz_id,
            "answers": [
                {
                    "question_id": question["id"],
                    "selected_option_id": correct_option["id"],
                }
            ],
        }

        response1 = self.client.post(f"/api/v1/quiz/{quiz_id}/submit", json=submission1)
        assert response1.status_code == 200
        result1 = response1.json()
        assert result1["score"] == 1

        # Second attempt - incorrect answer
        incorrect_option = next(
            opt for opt in question["options"] if not opt["is_correct"]
        )
        submission2 = {
            "quiz_id": quiz_id,
            "answers": [
                {
                    "question_id": question["id"],
                    "selected_option_id": incorrect_option["id"],
                }
            ],
        }

        response2 = self.client.post(f"/api/v1/quiz/{quiz_id}/submit", json=submission2)
        assert response2.status_code == 200
        result2 = response2.json()
        assert result2["score"] == 0

        # Check quiz attempts
        response = self.client.get(f"/api/v1/quiz/{quiz_id}/attempts")
        assert response.status_code == 200
        attempts = response.json()
        assert len(attempts) == 2

        # Verify attempt scores
        scores = [attempt["score"] for attempt in attempts]
        assert 1 in scores  # First attempt
        assert 0 in scores  # Second attempt

    def test_empty_quiz_submission(self):
        """Test submitting a quiz with no answers."""
        # Generate a quiz
        with patch("app.services.gemini_service.gemini_service") as mock_gemini:
            mock_gemini.validate_topic.return_value = True
            mock_gemini.generate_quiz = AsyncMock(
                return_value=GeminiQuizResponse(
                    topic="Test",
                    questions=[
                        GeneratedQuizQuestion(
                            question="Test question?",
                            options={
                                "A": "Answer A",
                                "B": "Answer B",
                                "C": "Answer C",
                                "D": "Answer D",
                            },
                            correct_answer="A",
                        )
                    ],
                )
            )

            response = self.client.post("/api/v1/quiz/generate", json={"topic": "Test"})

            quiz_id = response.json()["id"]

        # Submit with empty answers
        submission = {"quiz_id": quiz_id, "answers": []}

        response = self.client.post(f"/api/v1/quiz/{quiz_id}/submit", json=submission)
        assert response.status_code == 200

        result = response.json()
        assert result["score"] == 0
        assert result["total_questions"] == 1
        assert result["percentage"] == 0.0
