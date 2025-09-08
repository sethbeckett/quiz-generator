"""
Service layer for quiz-related business logic.
"""

import logging
from typing import Any

from sqlalchemy.orm import Session

from ..models.quiz import Question, QuestionOption, Quiz, QuizAttempt, UserResponse
from ..schemas.quiz import GeminiQuizResponse, QuizResult, QuizSubmission
from . import gemini_service as gemini_module

logger = logging.getLogger(__name__)

# Allow tests to override the gemini service via this module attribute
gemini_service = None


def get_gemini_service() -> Any:
    """Return the active gemini service instance, supporting test overrides."""
    global gemini_service
    return (
        gemini_service
        if gemini_service is not None
        else getattr(gemini_module, "gemini_service", None)
    )


class QuizService:
    """Service for managing quiz operations."""

    def __init__(self, db: Session):
        """Initialize quiz service with database session."""
        self.db = db

    async def generate_quiz(self, topic: str) -> Quiz | None:
        """
        Generate a new quiz using Gemini API and save to database.

        Args:
            topic: The topic for the quiz

        Returns:
            Created Quiz object or None if generation fails
        """
        # Validate topic
        service = get_gemini_service()
        if service is None or not service.validate_topic(topic):
            logger.warning(f"Invalid topic provided: {topic}")
            return None

        # Generate quiz using Gemini API
        service = get_gemini_service()
        gemini_response = await service.generate_quiz(topic) if service else None
        if not gemini_response:
            logger.error(f"Failed to generate quiz for topic: {topic}")
            return None

        # Create quiz in database
        try:
            quiz = self._create_quiz_from_gemini_response(gemini_response)
            self.db.add(quiz)
            self.db.commit()
            self.db.refresh(quiz)

            logger.info(f"Successfully created quiz {quiz.id} for topic: {topic}")
            return quiz

        except Exception as e:
            logger.error(f"Failed to save quiz to database: {e}")
            self.db.rollback()
            return None

    def _create_quiz_from_gemini_response(
        self, gemini_response: GeminiQuizResponse
    ) -> Quiz:
        """
        Convert Gemini API response to database models.

        Args:
            gemini_response: Response from Gemini API

        Returns:
            Quiz object with questions and options
        """
        quiz = Quiz(topic=gemini_response.topic)

        for idx, q_data in enumerate(gemini_response.questions):
            question = Question(question_text=q_data.question, question_order=idx + 1)

            # Create options for the question
            for letter, option_text in q_data.options.items():
                option = QuestionOption(
                    option_text=option_text,
                    option_letter=letter,
                    is_correct=(letter == q_data.correct_answer),
                )
                question.options.append(option)

            quiz.questions.append(question)

        return quiz

    def get_quiz_by_id(self, quiz_id: int) -> Quiz | None:
        """
        Retrieve a quiz by its ID.

        Args:
            quiz_id: The ID of the quiz

        Returns:
            Quiz object or None if not found
        """
        return self.db.query(Quiz).filter(Quiz.id == quiz_id).first()

    def get_all_quizzes(self, limit: int = 20, offset: int = 0) -> list[Quiz]:
        """
        Retrieve all quizzes with pagination.

        Args:
            limit: Maximum number of quizzes to return
            offset: Number of quizzes to skip

        Returns:
            List of Quiz objects
        """
        return (
            self.db.query(Quiz)
            .order_by(Quiz.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def submit_quiz_answers(self, submission: QuizSubmission) -> QuizResult | None:
        """
        Process quiz submission and calculate results.

        Args:
            submission: User's quiz answers

        Returns:
            QuizResult object or None if processing fails
        """
        try:
            # Get the quiz
            quiz = self.get_quiz_by_id(submission.quiz_id)
            if not quiz:
                logger.error(f"Quiz {submission.quiz_id} not found")
                return None

            # Create quiz attempt with default score (will be updated later)
            attempt = QuizAttempt(
                quiz_id=quiz.id,
                total_questions=len(quiz.questions),
                score=0,  # Initialize with 0, will be updated with actual score
            )
            self.db.add(attempt)
            self.db.flush()  # Get the attempt ID

            # Process each answer
            correct_count = 0
            correct_answers = []

            for answer in submission.answers:
                # Get the question and selected option
                question = next(
                    (q for q in quiz.questions if q.id == answer.question_id), None
                )
                if not question:
                    continue

                selected_option = next(
                    (
                        opt
                        for opt in question.options
                        if opt.id == answer.selected_option_id
                    ),
                    None,
                )
                if not selected_option:
                    continue

                # Check if answer is correct
                is_correct = selected_option.is_correct
                if is_correct:
                    correct_count += 1

                # Record the response
                user_response = UserResponse(
                    attempt_id=attempt.id,
                    question_id=question.id,
                    selected_option_id=selected_option.id,
                    is_correct=is_correct,
                )
                self.db.add(user_response)

                # Collect correct answer info for response
                correct_option = next(
                    (opt for opt in question.options if opt.is_correct), None
                )
                correct_answers.append(
                    {
                        "question_id": question.id,
                        "question_text": question.question_text,
                        "correct_option": correct_option.option_letter
                        if correct_option
                        else "N/A",
                        "correct_text": correct_option.option_text
                        if correct_option
                        else "N/A",
                        "user_selected": selected_option.option_letter,
                        "user_selected_text": selected_option.option_text,
                        "is_correct": is_correct,
                    }
                )

            # Update attempt with final score
            attempt.score = correct_count  # type: ignore[assignment]

            # Commit all changes
            self.db.commit()

            # Calculate percentage
            percentage = (
                (correct_count / len(quiz.questions)) * 100 if quiz.questions else 0
            )

            return QuizResult(
                score=correct_count,
                total_questions=len(quiz.questions),
                percentage=round(percentage, 2),
                correct_answers=correct_answers,
            )

        except Exception as e:
            logger.error(f"Failed to process quiz submission: {e}")
            self.db.rollback()
            return None

    def get_quiz_attempts(self, quiz_id: int) -> list[QuizAttempt]:
        """
        Get all attempts for a specific quiz.

        Args:
            quiz_id: The ID of the quiz

        Returns:
            List of QuizAttempt objects
        """
        return (
            self.db.query(QuizAttempt)
            .filter(QuizAttempt.quiz_id == quiz_id)
            .order_by(QuizAttempt.attempted_at.desc())
            .all()
        )
