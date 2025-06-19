import uuid
import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Post(Base):
    """
    Модель пользовательского поста (публикации).
    """
    __tablename__ = "posts"


    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=False)
    name = Column(String(200), nullable=False)
    tags = Column(String(255), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.datetime.now(datetime.timezone.utc)
    )