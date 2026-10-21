from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    full_name: Optional[str] = None
    college: Optional[str] = None
    major: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    full_name: Optional[str] = None
    college: Optional[str] = None
    major: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
