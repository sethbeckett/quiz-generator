"""
Database models for quiz-related entities.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Quiz(Base):
    """Quiz model representing a generated quiz."""

    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    questions = relationship(
        "Question", back_populates="quiz", cascade="all, delete-orphan"
    )
    attempts = relationship(
        "QuizAttempt", back_populates="quiz", cascade="all, delete-orphan"
    )


class Question(Base):
    """Question model representing a quiz question."""

    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_order = Column(Integer, nullable=False)

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    options = relationship(
        "QuestionOption", back_populates="question", cascade="all, delete-orphan"
    )


class QuestionOption(Base):
    """Question option model representing multiple choice options."""

    __tablename__ = "question_options"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    option_text = Column(Text, nullable=False)
    option_letter = Column(String(1), nullable=False)  # A, B, C, D
    is_correct = Column(Boolean, default=False, nullable=False)

    # Relationships
    question = relationship("Question", back_populates="options")


class QuizAttempt(Base):
    """Quiz attempt model representing a user's attempt at a quiz."""

    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    attempted_at = Column(DateTime(timezone=True), server_default=func.now())
    score = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)

    # Relationships
    quiz = relationship("Quiz", back_populates="attempts")
    responses = relationship(
        "UserResponse", back_populates="attempt", cascade="all, delete-orphan"
    )


class UserResponse(Base):
    """User response model representing a user's answer to a question."""

    __tablename__ = "user_responses"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    selected_option_id = Column(
        Integer, ForeignKey("question_options.id"), nullable=False
    )
    is_correct = Column(Boolean, nullable=False)

    # Relationships
    attempt = relationship("QuizAttempt", back_populates="responses")
    question = relationship("Question")
    selected_option = relationship("QuestionOption")
