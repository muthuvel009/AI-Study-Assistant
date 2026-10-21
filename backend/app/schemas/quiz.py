import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class QuizGenerateRequest(BaseModel):
    document_id: Optional[str] = None
    topic: str = Field(..., min_length=1, max_length=255)
    difficulty: str = Field(default="Medium")
    num_questions: int = Field(default=5, ge=1, le=20)

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        clean = v.capitalize()
        if clean not in ["Easy", "Medium", "Hard"]:
            return "Medium"
        return clean


class SafeQuestionResponse(BaseModel):
    id: str
    question_text: str
    options: List[str]
    topic: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("options", mode="before")
    @classmethod
    def parse_options(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [v]
        return list(v) if v else []


class SafeQuizResponse(BaseModel):
    id: str
    title: str
    topic: Optional[str] = None
    difficulty: str = "Medium"
    document_id: Optional[str] = None
    created_at: datetime
    questions: List[SafeQuestionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class QuizListItem(BaseModel):
    id: str
    title: str
    topic: Optional[str] = None
    difficulty: str = "Medium"
    score: Optional[float] = None
    created_at: datetime
    total_questions: int = 0

    model_config = ConfigDict(from_attributes=True)


class QuizSubmitRequest(BaseModel):
    answers: Dict[str, str] = Field(..., description="Mapping of question_id to selected option string")


class QuestionResultItem(BaseModel):
    question_id: str
    question_text: str
    options: List[str]
    student_answer: Optional[str] = None
    correct_answer: str
    is_correct: bool
    explanation: Optional[str] = None
    topic: Optional[str] = None


class QuizResultsResponse(BaseModel):
    quiz_id: str
    title: str
    topic: Optional[str] = None
    difficulty: str = "Medium"
    score: float
    percentage: float
    total_questions: int
    correct_count: int
    question_results: List[QuestionResultItem] = []
    created_at: datetime
