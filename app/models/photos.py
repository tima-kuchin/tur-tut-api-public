import uuid
import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Photo(Base):
    """
    Модель фотографии, загруженной пользователем.
    Фотография может быть привязана к любой сущности (маршрут, пост, комментарий)
    через полиморфную связь: target_type_id + target_uuid.
    """
    __tablename__ = "photos"


    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=False)
    target_type_id = Column(UUID(as_uuid=True), ForeignKey("target_types.uuid"), nullable=True)
    target_uuid = Column(UUID(as_uuid=True), nullable=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.datetime.now(datetime.timezone.utc)
    )
