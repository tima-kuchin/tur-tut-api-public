import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field

class CommentCreate(BaseModel):
    comment_text: str = Field(..., min_length=1, max_length=2000, description="Текст комментария")

class CommentOut(BaseModel):
    uuid: UUID
    comment_text: str
    created_at: datetime.datetime
    creator_login: str
    creator_avatar: Optional[str]
    likes_count: int = 0
    is_liked: bool = False

    class Config:
        from_attributes = True
