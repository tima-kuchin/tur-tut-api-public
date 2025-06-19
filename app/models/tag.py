import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base

class RouteTag(Base):
    """
    Справочник тегов для маршрутов.
    """
    __tablename__ = "route_tags"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_tag_name = Column(String(100), nullable=False)

class PostTag(Base):
    """
    Справочник тегов для постов.
    """
    __tablename__ = "post_tags"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_tag_name = Column(String(100), nullable=False)