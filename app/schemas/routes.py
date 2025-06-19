from datetime import datetime

from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.users import UserRole
from app.schemas.waypoints import WaypointOut, WaypointCreate


class RouteBase(BaseModel):
    name: str = Field(..., min_length=1, description="Название маршрута")
    location: Optional[str] = Field(None, description="Локация маршрута")
    description: Optional[str] = Field(None, description="Описание маршрута")
    route_type_uuid: Optional[UUID] = Field(None, description="UUID типа маршрута")
    geo_data: Optional[str] = Field(None, description="WKT-строка")
    tags: Optional[List[UUID]] = []
    duration: Optional[int] = Field(None, description="Длительность в минутах")
    distance: Optional[float] = Field(None, description="Расстояние в км")
    difficulty_uuid: Optional[UUID] = Field(None, description="UUID сложности маршрута")
    is_public: Optional[bool] = Field(False, description="Публичность")
    published_at: Optional[datetime] = Field(None, description="Дата публикации")

class RouteCreate(RouteBase):
    waypoints: Optional[List[WaypointCreate]] = []

class RouteUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    route_type_uuid: Optional[UUID] = None
    geo_data: Optional[str] = None
    tags: Optional[List[UUID]] = None
    duration: Optional[int] = None
    distance: Optional[float] = None
    difficulty_uuid: Optional[UUID] = None
    is_public: Optional[bool] = None
    published_at: Optional[datetime] = None
    waypoints: Optional[List[WaypointCreate]] = None
    thumbnail_url: Optional[str] = None

class RouteOut(RouteBase):
    uuid: UUID
    created_at: datetime
    edited_at: Optional[datetime] = None
    last_edited_by_uuid: Optional[UUID] = None
    last_edited_by_role: Optional[UserRole] = None
    waypoints: List[WaypointOut] = []
    likes_count: int = 0
    comments_count: int = 0
    is_liked: bool = False
    is_favorite: bool = False
    thumbnail_url: Optional[str] = None
    creator_login: Optional[str] = None
    route_type_name: Optional[str] = None
    difficulty_type_name: Optional[str] = None
    can_edit: bool = False
    can_delete: bool = False
    tags: Optional[List[UUID]] = None

    class Config:
        from_attributes = True

class RouteCardOut(BaseModel):
    uuid: UUID
    name: str
    location: str
    avg_rating: Optional[float] = None
    likes_count: int
    comments_count: int
    is_favorite: bool = False
    is_liked: bool = False
    thumbnail_url: Optional[str] = None
    route_type_uuid: Optional[UUID] = None
    route_type_name: Optional[str] = None

    class Config:
        from_attributes = True