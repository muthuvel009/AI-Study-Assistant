from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User, Recommendation
from app.schemas.recommendation import RecommendationResponse
from app.services.recommendation_service import generate_recommendations_for_user

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])


@router.get("", response_model=List[RecommendationResponse])
def get_recommendations_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve active study recommendations for authenticated student.
    Returns authentic empty list for new students.
    """
    recs = (
        db.query(Recommendation)
        .filter(Recommendation.user_id == current_user.id)
        .order_by(Recommendation.created_at.desc())
        .all()
    )
    return recs


@router.post("/generate", response_model=List[RecommendationResponse])
def generate_recommendations_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Regenerate recommendations based on recent learning signals, mastery levels, and quiz attempts.
    """
    return generate_recommendations_for_user(current_user.id, db)


@router.get("/{rec_id}", response_model=RecommendationResponse)
def get_single_recommendation(
    rec_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve details for a specific recommendation.
    """
    rec = (
        db.query(Recommendation)
        .filter(Recommendation.id == rec_id, Recommendation.user_id == current_user.id)
        .first()
    )
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found.")
    return rec
