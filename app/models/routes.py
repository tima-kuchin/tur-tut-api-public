import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Integer,
    Float,
    Boolean,
    ForeignKey,
    func,
    Enum
)
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.models.users import UserRole


class Route(Base):
    """
    Модель туристического маршрута.
    """
    __tablename__ = "routes"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=False)
    name = Column(String(200), nullable=False)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    route_type_uuid = Column(UUID(as_uuid=True), ForeignKey("route_types.uuid"), nullable=True)
    geo_data = Column(Geometry("LINESTRING", srid=4326), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    duration = Column(Integer, nullable=True)
    distance = Column(Float, nullable=True)
    difficulty_uuid = Column(UUID(as_uuid=True), ForeignKey("difficulties_types.uuid"), nullable=True)
    avg_rating = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    edited_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    is_public = Column(Boolean, nullable=False, default=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    last_edited_by_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=True)
    last_edited_by_role = Column(Enum(UserRole, name="user_role_enum"), nullable=True)
    route_type = relationship("RouteType", backref="routes", lazy="joined")
    difficulty_type = relationship("DifficultyType", backref="routes", lazy="joined")
    creator = relationship("DBUser", backref="routes_created", foreign_keys=[creator_uuid])
    waypoints = relationship("Waypoint", back_populates="route", cascade="all, delete-orphan")
    last_editor = relationship("DBUser", foreign_keys=[last_edited_by_uuid])
    tags = relationship("RouteTag",secondary="routes_route_tags", backref="routes")
    likes = relationship("RouteLike", cascade="all, delete-orphan", passive_deletes=True, backref="route")
    favorites = relationship("RouteFavorite", cascade="all, delete-orphan", passive_deletes=True,  backref="route")