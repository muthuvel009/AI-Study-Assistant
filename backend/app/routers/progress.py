from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User, Progress, Quiz, Document
from app.schemas.progress import (
    TopicProgressResponse,
    ProgressSummaryResponse,
    ProgressActivityItem,
    ProgressActivityResponse,
)

router = APIRouter(prefix="/api/progress", tags=["Progress"])


@router.get("", response_model=List[TopicProgressResponse])
def get_user_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve topic mastery records for the authenticated student."""
    records = (
        db.query(Progress)
        .filter(Progress.user_id == current_user.id)
        .order_by(Progress.mastery_score.desc())
        .all()
    )
    return records


@router.get("/summary", response_model=ProgressSummaryResponse)
def get_progress_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve overall progress summary. Returns authentic zero-state for new students."""
    records = (
        db.query(Progress)
        .filter(Progress.user_id == current_user.id)
        .all()
    )

    if not records:
        return ProgressSummaryResponse(
            total_questions_answered=0,
            correct_answers=0,
            average_mastery=0.0,
            topics=[],
        )

    total_attempted = sum(r.questions_attempted for r in records)
    total_correct = sum(r.questions_correct for r in records)
    avg_mastery = sum(r.mastery_score for r in records) / len(records) if records else 0.0

    return ProgressSummaryResponse(
        total_questions_answered=total_attempted,
        correct_answers=total_correct,
        average_mastery=round(avg_mastery, 1),
        topics=[TopicProgressResponse.model_validate(r) for r in records],
    )


@router.get("/activity", response_model=ProgressActivityResponse)
def get_recent_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve recent learning activities (quizzes taken, documents uploaded)."""
    activities: List[ProgressActivityItem] = []

    # Completed quizzes
    quizzes = (
        db.query(Quiz)
        .filter(Quiz.user_id == current_user.id, Quiz.score.isnot(None))
        .order_by(Quiz.created_at.desc())
        .limit(10)
        .all()
    )
    for q in quizzes:
        activities.append(
            ProgressActivityItem(
                id=q.id,
                activity_type="quiz_completed",
                title=f"Completed {q.title} ({q.difficulty})",
                topic=q.topic,
                score=q.score,
                timestamp=q.created_at,
            )
        )

    # Documents uploaded
    docs = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .limit(5)
        .all()
    )
    for d in docs:
        activities.append(
            ProgressActivityItem(
                id=d.id,
                activity_type="document_uploaded",
                title=f"Uploaded {d.filename}",
                topic=None,
                score=None,
                timestamp=d.created_at,
            )
        )

    # Sort combined activities by timestamp descending
    activities.sort(key=lambda a: a.timestamp, reverse=True)
    return ProgressActivityResponse(activities=activities[:15])


@router.get("/{topic}", response_model=TopicProgressResponse)
def get_topic_progress(
    topic: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve progress for a specific study topic."""
    record = (
        db.query(Progress)
        .filter(Progress.user_id == current_user.id, Progress.topic == topic)
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No progress recorded for topic '{topic}'.",
        )
    return record
