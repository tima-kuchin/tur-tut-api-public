from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.db.session import get_db
from app.dependencies.security import get_current_user
from app.models.users import DBUser
from app.schemas.waypoints import WaypointCreate, WaypointUpdate, WaypointOut
from app.crud import waypoints as waypoints_crud

router = APIRouter(prefix="/waypoints", tags=["waypoints"])


@router.get("/{route_id}/waypoints", response_model=List[WaypointOut])
def get_waypoints(route_id: UUID, db: Session = Depends(get_db)):
    return waypoints_crud.get_waypoints(db, route_id)


@router.get("/{route_id}/waypoints/{waypoint_id}", response_model=WaypointOut)
def get_waypoint(
    route_id: UUID,
    waypoint_id: UUID,
    db: Session = Depends(get_db),
):
    return waypoints_crud.get_waypoint(db, route_id, waypoint_id)

@router.post("/{route_id}/waypoints", response_model=WaypointOut)
def add_waypoint(
    route_id: UUID,
    waypoint_data: WaypointCreate,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    return waypoints_crud.add_waypoint(db, route_id, waypoint_data, current_user)

@router.put("/{route_id}/waypoints/{waypoint_id}", response_model=WaypointOut)
def update_waypoint(
    route_id: UUID,
    waypoint_id: UUID,
    waypoint_data: WaypointUpdate,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    return waypoints_crud.update_waypoint(db, route_id, waypoint_id, waypoint_data, current_user)


@router.delete("/{route_id}/waypoints/{waypoint_id}")
def delete_waypoint(
    route_id: UUID,
    waypoint_id: UUID,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    waypoints_crud.delete_waypoint(db, route_id, waypoint_id, current_user)
    return {"detail": "Точка удалена"}