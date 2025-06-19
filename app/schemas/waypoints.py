from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field

class WaypointBase(BaseModel):
    lat: float = Field(..., description="Широта")
    lon: float = Field(..., description="Долгота")
    description: Optional[str] = Field(None, description="Описание")
    photo_url: Optional[str] = Field(None, description="Ссылка на фото")

class WaypointCreate(WaypointBase):
    type: Optional[str] = None

class WaypointUpdate(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None
    type: Optional[str] = None
    description: Optional[str] = None
    photo_url: Optional[str] = None

class WaypointOut(WaypointBase):
    uuid: UUID
    order: Optional[int] = None
    type: str

    class Config:
        from_attributes = True