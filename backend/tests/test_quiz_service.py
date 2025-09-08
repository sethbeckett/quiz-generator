"""
Tests for quiz service functionality.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.quiz import Question, QuestionOption, Quiz, QuizAttempt, UserResponse
from app.schemas.quiz import (
    GeminiQuizResponse,
    GeneratedQuizQuestion,
    QuizSubmission,
    UserAnswerSubmission,
)
from app.services.quiz_service import QuizService


class TestQuizService:
    """Test suite for QuizService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.quiz_service = QuizService(self.mock_db)

    def test_create_quiz_from_gemini_response(self):
        """Test creating quiz from Gemini API response."""
        # Mock Gemini response
        gemini_response = GeminiQuizResponse(
            topic="Test Topic",
            questions=[
                GeneratedQuizQuestion(
                    question="What is 2+2?",
                    options={"A": "3", "B": "4", "C": "5", "D": "6"},
                    correct_answer="B",
                    explanation="Basic arithmetic",
                )
            ],
        )

        # Create quiz from response
        quiz = self.quiz_service._create_quiz_from_gemini_response(gemini_response)

        # Assertions
        assert quiz.topic == "Test Topic"
        assert len(quiz.questions) == 1

        question = quiz.questions[0]
        assert question.question_text == "What is 2+2?"
        assert question.question_order == 1
        assert len(question.options) == 4

        # Check correct answer
        correct_option = next(opt for opt in question.options if opt.is_correct)
        assert correct_option.option_letter == "B"
        assert correct_option.option_text == "4"

    @pytest.mark.asyncio
    async def test_generate_quiz_success(self):
        """Test successful quiz generation."""
        # Mock the gemini service
        with patch("app.services.quiz_service.gemini_service") as mock_gemini:
            mock_gemini.validate_topic.return_value = True
            mock_gemini.generate_quiz = AsyncMock(
                return_value=GeminiQuizResponse(
                    topic="Python",
                    questions=[
                        GeneratedQuizQuestion(
                            question="What is Python?",
                            options={
                                "A": "Snake",
                                "B": "Language",
                                "C": "Tool",
                                "D": "Framework",
                            },
                            correct_answer="B",
                        )
                    ],
                )
            )

            # Mock database operations
            self.mock_db.add = Mock()
            self.mock_db.commit = Mock()
            self.mock_db.refresh = Mock()

            # Test quiz generation
            result = await self.quiz_service.generate_quiz("Python")

            # Assertions
            assert result is not None
            assert result.topic == "Python"
            self.mock_db.add.assert_called_once()
            self.mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_quiz_invalid_topic(self):
        """Test quiz generation with invalid topic."""
        with patch("app.services.quiz_service.gemini_service") as mock_gemini:
            mock_gemini.validate_topic.return_value = False

            result = await self.quiz_service.generate_quiz("")

            assert result is None

    def test_submit_quiz_answers_success(self):
        """Test successful quiz submission with correct answers."""
        # Create a mock quiz with questions and options
        quiz = Quiz(id=1, topic="Test Quiz")

        # Question 1: 2+2=4 (correct answer is B)
        question1 = Question(
            id=1,
            quiz=quiz,
            question_text="What is 2+2?",
            question_order=1
        )
        option1a = QuestionOption(id=1, question=question1, option_letter="A", option_text="3", is_correct=False)
        option1b = QuestionOption(id=2, question=question1, option_letter="B", option_text="4", is_correct=True)
        option1c = QuestionOption(id=3, question=question1, option_letter="C", option_text="5", is_correct=False)
        option1d = QuestionOption(id=4, question=question1, option_letter="D", option_text="6", is_correct=False)
        question1.options = [option1a, option1b, option1c, option1d]

        # Question 2: 3*3=9 (correct answer is C)
        question2 = Question(
            id=2,
            quiz=quiz,
            question_text="What is 3*3?",
            question_order=2
        )
        option2a = QuestionOption(id=5, question=question2, option_letter="A", option_text="6", is_correct=False)
        option2b = QuestionOption(id=6, question=question2, option_letter="B", option_text="8", is_correct=False)
        option2c = QuestionOption(id=7, question=question2, option_letter="C", option_text="9", is_correct=True)
        option2d = QuestionOption(id=8, question=question2, option_letter="D", option_text="12", is_correct=False)
        question2.options = [option2a, option2b, option2c, option2d]

        quiz.questions = [question1, question2]

        # Mock database operations
        self.quiz_service.get_quiz_by_id = Mock(return_value=quiz)
        self.mock_db.add = Mock()
        self.mock_db.flush = Mock()
        self.mock_db.commit = Mock()

        # Create submission with all correct answers
        submission = QuizSubmission(
            quiz_id=1,
            answers=[
                UserAnswerSubmission(question_id=1, selected_option_id=2),  # Correct: B
                UserAnswerSubmission(question_id=2, selected_option_id=7),  # Correct: C
            ]
        )

        # Test submission
        result = self.quiz_service.submit_quiz_answers(submission)

        # Assertions
        assert result is not None
        assert result.score == 2  # Both answers correct
        assert result.total_questions == 2
        assert result.percentage == 100.0
        assert len(result.correct_answers) == 2

        # Check that database operations were called
        self.mock_db.add.assert_called()  # Should add QuizAttempt and UserResponses
        self.mock_db.flush.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_submit_quiz_answers_partial_correct(self):
        """Test quiz submission with some correct and some incorrect answers."""
        # Create a mock quiz (same as above)
        quiz = Quiz(id=1, topic="Test Quiz")

        question1 = Question(id=1, quiz=quiz, question_text="What is 2+2?", question_order=1)
        option1a = QuestionOption(id=1, question=question1, option_letter="A", option_text="3", is_correct=False)
        option1b = QuestionOption(id=2, question=question1, option_letter="B", option_text="4", is_correct=True)
        question1.options = [option1a, option1b]

        question2 = Question(id=2, quiz=quiz, question_text="What is 3*3?", question_order=2)
        option2a = QuestionOption(id=5, question=question2, option_letter="A", option_text="6", is_correct=False)
        option2c = QuestionOption(id=7, question=question2, option_letter="C", option_text="9", is_correct=True)
        question2.options = [option2a, option2c]

        quiz.questions = [question1, question2]

        # Mock database operations
        self.quiz_service.get_quiz_by_id = Mock(return_value=quiz)
        self.mock_db.add = Mock()
        self.mock_db.flush = Mock()
        self.mock_db.commit = Mock()

        # Create submission with one correct, one incorrect
        submission = QuizSubmission(
            quiz_id=1,
            answers=[
                UserAnswerSubmission(question_id=1, selected_option_id=2),  # Correct: B
                UserAnswerSubmission(question_id=2, selected_option_id=5),  # Incorrect: A
            ]
        )

        # Test submission
        result = self.quiz_service.submit_quiz_answers(submission)

        # Assertions
        assert result is not None
        assert result.score == 1  # One correct answer
        assert result.total_questions == 2
        assert result.percentage == 50.0
        assert len(result.correct_answers) == 2

        # Check individual answer results
        answer_1 = next(a for a in result.correct_answers if a["question_id"] == 1)
        answer_2 = next(a for a in result.correct_answers if a["question_id"] == 2)

        assert answer_1["is_correct"] is True
        assert answer_2["is_correct"] is False

    def test_submit_quiz_answers_quiz_not_found(self):
        """Test quiz submission when quiz doesn't exist."""
        # Mock quiz not found
        self.quiz_service.get_quiz_by_id = Mock(return_value=None)

        submission = QuizSubmission(
            quiz_id=999,
            answers=[UserAnswerSubmission(question_id=1, selected_option_id=1)]
        )

        result = self.quiz_service.submit_quiz_answers(submission)

        assert result is None

    def test_submit_quiz_answers_invalid_question_id(self):
        """Test quiz submission with invalid question ID."""
        # Create a quiz with one question
        quiz = Quiz(id=1, topic="Test Quiz")
        question = Question(id=1, quiz=quiz, question_text="Test?", question_order=1)
        option = QuestionOption(id=1, question=question, option_letter="A", option_text="Answer", is_correct=True)
        question.options = [option]
        quiz.questions = [question]

        self.quiz_service.get_quiz_by_id = Mock(return_value=quiz)
        self.mock_db.add = Mock()
        self.mock_db.flush = Mock()
        self.mock_db.commit = Mock()

        # Submit answer for non-existent question
        submission = QuizSubmission(
            quiz_id=1,
            answers=[UserAnswerSubmission(question_id=999, selected_option_id=1)]  # Invalid question ID
        )

        result = self.quiz_service.submit_quiz_answers(submission)

        # Should still return result, but with 0 score since no valid answers
        assert result is not None
        assert result.score == 0
        assert result.total_questions == 1
        assert result.percentage == 0.0

    def test_submit_quiz_answers_invalid_option_id(self):
        """Test quiz submission with invalid option ID."""
        # Create a quiz
        quiz = Quiz(id=1, topic="Test Quiz")
        question = Question(id=1, quiz=quiz, question_text="Test?", question_order=1)
        option = QuestionOption(id=1, question=question, option_letter="A", option_text="Answer", is_correct=True)
        question.options = [option]
        quiz.questions = [question]

        self.quiz_service.get_quiz_by_id = Mock(return_value=quiz)
        self.mock_db.add = Mock()
        self.mock_db.flush = Mock()
        self.mock_db.commit = Mock()

        # Submit answer with invalid option ID
        submission = QuizSubmission(
            quiz_id=1,
            answers=[UserAnswerSubmission(question_id=1, selected_option_id=999)]  # Invalid option ID
        )

        result = self.quiz_service.submit_quiz_answers(submission)

        # Should still return result, but with 0 score since no valid answers
        assert result is not None
        assert result.score == 0
        assert result.total_questions == 1
        assert result.percentage == 0.0
