from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict


class ChatMessageCreate(BaseModel):
    query: str
    document_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    id: str
    sender: str
    text: str
    sources: List[Any] = []
    timestamp: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSendResponse(BaseModel):
    answer: str
    response: str
    sources: List[Any] = []
    chat_id: str
    document_id: Optional[str] = None
