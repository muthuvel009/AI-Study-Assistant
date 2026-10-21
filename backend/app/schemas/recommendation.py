from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class RecommendationResponse(BaseModel):
    id: str
    title: str
    description: str
    topic: Optional[str] = None
    priority: str = "medium"
    recommendation_type: str = "Revision"
    reason: Optional[str] = None
    action_label: str = "Practice Now"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
