"""
API routes for quiz operations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.quiz import (
    FeedbackRequest,
    FeedbackResponse,
    QuizAttemptResponse,
    QuizCreate,
    QuizResponse,
    QuizResult,
    QuizSubmission,
)
from ..services import gemini_service as gemini_module
from ..services import quiz_service as quiz_service_module
from ..services.quiz_service import QuizService

router = APIRouter(prefix="/quiz", tags=["quiz"])


@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(quiz_data: QuizCreate, db: Session = Depends(get_db)):
    """
    Generate a new quiz based on the provided topic.

    Args:
        quiz_data: Quiz creation data containing the topic
        db: Database session

    Returns:
        Generated quiz with questions and options

    Raises:
        HTTPException: If quiz generation fails
    """
    quiz_service = QuizService(db)

    quiz = await quiz_service.generate_quiz(quiz_data.topic)
    if not quiz:
        raise HTTPException(
            status_code=400,
            detail="Failed to generate quiz. Please check your topic and try again.",
        )

    return quiz


@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific quiz by ID.

    Args:
        quiz_id: The ID of the quiz to retrieve
        db: Database session

    Returns:
        Quiz with questions and options

    Raises:
        HTTPException: If quiz is not found
    """
    quiz_service = QuizService(db)

    quiz = quiz_service.get_quiz_by_id(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail=f"Quiz with ID {quiz_id} not found")

    return quiz


@router.get("/", response_model=list[QuizResponse])
def list_quizzes(limit: int = 20, offset: int = 0, db: Session = Depends(get_db)):
    """
    List all quizzes with pagination.

    Args:
        limit: Maximum number of quizzes to return (default: 20)
        offset: Number of quizzes to skip (default: 0)
        db: Database session

    Returns:
        List of quizzes
    """
    quiz_service = QuizService(db)
    return quiz_service.get_all_quizzes(limit=limit, offset=offset)


@router.post("/{quiz_id}/submit", response_model=QuizResult)
def submit_quiz(
    quiz_id: int, submission: QuizSubmission, db: Session = Depends(get_db)
):
    """
    Submit answers for a quiz and get results.

    Args:
        quiz_id: The ID of the quiz being submitted
        submission: User's answers to the quiz
        db: Database session

    Returns:
        Quiz results with score and correct answers

    Raises:
        HTTPException: If submission processing fails
    """
    # Validate that the quiz_id matches the submission
    if quiz_id != submission.quiz_id:
        raise HTTPException(
            status_code=400,
            detail="Quiz ID in URL does not match quiz ID in submission",
        )

    quiz_service = QuizService(db)

    result = quiz_service.submit_quiz_answers(submission)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to process quiz submission")

    return result


@router.get("/{quiz_id}/attempts", response_model=list[QuizAttemptResponse])
def get_quiz_attempts(quiz_id: int, db: Session = Depends(get_db)):
    """
    Get all attempts for a specific quiz.

    Args:
        quiz_id: The ID of the quiz
        db: Database session

    Returns:
        List of quiz attempts

    Raises:
        HTTPException: If quiz is not found
    """
    quiz_service = QuizService(db)

    # First check if quiz exists
    quiz = quiz_service.get_quiz_by_id(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail=f"Quiz with ID {quiz_id} not found")

    return quiz_service.get_quiz_attempts(quiz_id)


@router.post("/{quiz_id}/feedback", response_model=FeedbackResponse)
async def get_quiz_feedback(
    quiz_id: int, payload: FeedbackRequest, db: Session = Depends(get_db)
):
    """
    Generate brief explanations for incorrect answers.

    Validates the quiz exists then delegates to the LLM service.
    """
    quiz_service = QuizService(db)
    quiz = quiz_service.get_quiz_by_id(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail=f"Quiz with ID {quiz_id} not found")

    # Prefer test-patched service; fallback to real gemini service if available
    service = getattr(quiz_service_module, 'gemini_service', None) or getattr(
        gemini_module, 'gemini_service', None
    )

    feedback = None
    if service is not None:
        feedback = await service.explain_incorrect_answers(payload)

    # Fallback: create concise deterministic explanations to avoid 500s in prod
    if not feedback:
        items = []
        for i in payload.items:
            text = (
                f"You chose {i.user_selected}. {i.user_selected_text}. "
                f"The correct answer is {i.correct_option}. {i.correct_text}."
            )
            items.append({"question_id": i.question_id, "explanation": text})
        return FeedbackResponse(items=items)  # type: ignore[arg-type]

    return feedback
