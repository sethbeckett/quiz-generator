"""
Pydantic schemas for request/response validation.
"""

from .quiz import (
    GeminiQuizResponse,
    GeneratedQuizQuestion,
    QuestionOptionResponse,
    QuestionResponse,
    QuizAttemptResponse,
    QuizCreate,
    QuizResponse,
    QuizResult,
    QuizSubmission,
    UserAnswerSubmission,
)

__all__ = [
    "QuizCreate",
    "QuizResponse",
    "QuizSubmission",
    "QuizResult",
    "QuestionResponse",
    "QuestionOptionResponse",
    "UserAnswerSubmission",
    "QuizAttemptResponse",
    "GeminiQuizResponse",
    "GeneratedQuizQuestion",
]
