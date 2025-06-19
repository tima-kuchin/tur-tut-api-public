import uuid
import datetime
import enum

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Gender(str, enum.Enum):
    male = "male"
    female = "female"


class UserRole(str, enum.Enum):
    user = "user"
    moderator = "moderator"
    admin = "admin"


class DBUser(Base):
    """
    Таблица 'users' предназначена для хранения профилей пользователей.
    """
    __tablename__ = "users"


    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    login = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    gender = Column(Enum(Gender, name="gender_enum"), nullable=True)
    role = Column(Enum(UserRole, name="user_role_enum"), nullable=False, default=UserRole.user)
    age = Column(Integer, nullable=True)
    profile_picture = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    is_blocked = Column(Boolean, nullable=False, default=False)
    block_reason = Column(Text, nullable=True)
    block_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.datetime.now(datetime.timezone.utc))
