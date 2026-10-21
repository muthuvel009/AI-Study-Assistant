import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User, Quiz, Question
from app.schemas.quiz import (
    QuizGenerateRequest,
    SafeQuizResponse,
    SafeQuestionResponse,
    QuizListItem,
    QuizSubmitRequest,
    QuizResultsResponse,
    QuestionResultItem,
)
from app.services.quiz_service import create_quiz_pipeline, grade_quiz_submission

router = APIRouter(prefix="/api/quizzes", tags=["Quizzes"])


@router.post("/generate", response_model=SafeQuizResponse, status_code=status.HTTP_201_CREATED)
def generate_quiz_endpoint(
    req: QuizGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate an AI adaptive quiz using semantic RAG retrieval over student study material.
    Returns safe questions without exposing correct answer keys or explanations.
    """
    quiz = create_quiz_pipeline(
        user_id=current_user.id,
        topic=req.topic,
        difficulty=req.difficulty,
        num_questions=req.num_questions,
        document_id=req.document_id,
        db=db,
    )

    # Construct safe response
    safe_questions = []
    for q in quiz.questions:
        options = json.loads(q.options) if isinstance(q.options, str) else q.options
        safe_questions.append(
            SafeQuestionResponse(
                id=q.id,
                question_text=q.question_text,
                options=options,
                topic=q.topic,
            )
        )

    return SafeQuizResponse(
        id=quiz.id,
        title=quiz.title,
        topic=quiz.topic,
        difficulty=quiz.difficulty,
        document_id=quiz.document_id,
        created_at=quiz.created_at,
        questions=safe_questions,
    )


@router.get("", response_model=List[QuizListItem])
def list_quizzes_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all generated quizzes belonging to the authenticated student.
    """
    quizzes = (
        db.query(Quiz)
        .filter(Quiz.user_id == current_user.id)
        .order_by(Quiz.created_at.desc())
        .all()
    )

    items = []
    for q in quizzes:
        q_count = db.query(Question).filter(Question.quiz_id == q.id).count()
        items.append(
            QuizListItem(
                id=q.id,
                title=q.title,
                topic=q.topic,
                difficulty=q.difficulty,
                score=q.score,
                created_at=q.created_at,
                total_questions=q_count,
            )
        )
    return items


@router.get("/{quiz_id}", response_model=SafeQuizResponse)
def get_quiz_endpoint(
    quiz_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve single quiz by ID. Answers remain hidden for active test-taking.
    """
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.user_id == current_user.id).first()
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found.")

    safe_questions = []
    for q in quiz.questions:
        options = json.loads(q.options) if isinstance(q.options, str) else q.options
        safe_questions.append(
            SafeQuestionResponse(
                id=q.id,
                question_text=q.question_text,
                options=options,
                topic=q.topic,
            )
        )

    return SafeQuizResponse(
        id=quiz.id,
        title=quiz.title,
        topic=quiz.topic,
        difficulty=quiz.difficulty,
        document_id=quiz.document_id,
        created_at=quiz.created_at,
        questions=safe_questions,
    )


@router.post("/{quiz_id}/submit", response_model=QuizResultsResponse)
def submit_quiz_endpoint(
    quiz_id: str,
    req: QuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit quiz answers for authoritative server-side scoring and mastery update.
    Returns detailed scoring results with explanations.
    """
    return grade_quiz_submission(
        quiz_id=quiz_id,
        user_id=current_user.id,
        user_answers=req.answers,
        db=db,
    )


@router.get("/{quiz_id}/results", response_model=QuizResultsResponse)
def get_quiz_results_endpoint(
    quiz_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve detailed results and explanations for an already completed quiz.
    """
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.user_id == current_user.id).first()
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found.")

    if quiz.score is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quiz has not been submitted yet. Complete and submit the quiz to view results.",
        )

    questions = db.query(Question).filter(Question.quiz_id == quiz.id).all()
    question_results = []
    correct_count = 0

    for q in questions:
        options = json.loads(q.options) if isinstance(q.options, str) else q.options
        question_results.append(
            QuestionResultItem(
                question_id=q.id,
                question_text=q.question_text,
                options=options,
                student_answer=None,
                correct_answer=q.correct_answer,
                is_correct=True,
                explanation=q.explanation,
                topic=q.topic,
            )
        )

    return QuizResultsResponse(
        quiz_id=quiz.id,
        title=quiz.title,
        topic=quiz.topic,
        difficulty=quiz.difficulty,
        score=quiz.score,
        percentage=quiz.score,
        total_questions=len(questions),
        correct_count=round((quiz.score / 100.0) * len(questions)) if questions else 0,
        question_results=question_results,
        created_at=quiz.created_at,
    )
