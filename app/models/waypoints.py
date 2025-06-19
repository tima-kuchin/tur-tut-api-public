import enum
import uuid
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base


class WaypointType(str, enum.Enum):
    start = "start"
    intermediate = "intermediate"
    finish = "finish"
    isolated = "isolated"


class Waypoint(Base):
    """
    Таблица 'waypoints' предназначена для хранения точек маршрутов.
    """
    __tablename__ = "waypoints"


    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_uuid = Column(UUID(as_uuid=True), ForeignKey("routes.uuid", ondelete="CASCADE"), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    order = Column(Integer, nullable=True)
    type = Column(Enum(WaypointType), nullable=False, default=WaypointType.intermediate)
    description = Column(Text, nullable=True)
    photo_url = Column(String, nullable=True)
    route = relationship("Route", back_populates="waypoints")