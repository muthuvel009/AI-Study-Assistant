from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class TopicProgressResponse(BaseModel):
    topic: str
    mastery_score: float
    questions_attempted: int
    questions_correct: int
    quiz_attempts: int = 0
    latest_score: Optional[float] = None
    average_score: Optional[float] = None
    last_studied_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProgressSummaryResponse(BaseModel):
    total_questions_answered: int = 0
    correct_answers: int = 0
    average_mastery: float = 0.0
    topics: List[TopicProgressResponse] = []


class ProgressActivityItem(BaseModel):
    id: str
    activity_type: str  # "quiz_completed", "document_uploaded"
    title: str
    topic: Optional[str] = None
    score: Optional[float] = None
    timestamp: datetime


class ProgressActivityResponse(BaseModel):
    activities: List[ProgressActivityItem] = []
