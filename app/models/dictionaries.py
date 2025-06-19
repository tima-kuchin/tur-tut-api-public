import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base

class RouteType(Base):
    """
    Модель RouteType представляет справочник типов маршрутов.
    """
    __tablename__ = "route_types"


    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)


class DifficultyType(Base):
    """
    Модель DifficultyType хранит информацию об уровнях сложности маршрутов.
    """
    __tablename__ = "difficulties_types"


    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)