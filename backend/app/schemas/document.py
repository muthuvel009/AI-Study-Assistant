from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class DocumentBase(BaseModel):
    filename: str


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_size: Optional[int] = None
    status: str
    chunks_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
