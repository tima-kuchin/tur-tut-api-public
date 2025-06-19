import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base

class TargetType(Base):
    """
    Таблица 'target_types' предназначена для хранения типов сущностей.
    """
    __tablename__ = "target_types"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False)