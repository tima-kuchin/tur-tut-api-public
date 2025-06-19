from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from app.dependencies.security import get_current_user, get_current_user_optional
from app.db.session import get_db
from app.models.users import DBUser
from app.crud import routes as route_crud
from app.schemas.routes import RouteCreate, RouteUpdate, RouteOut, RouteCardOut

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("/", response_model=List[RouteCardOut])
def list_routes(
    db: Session = Depends(get_db),
    current_user: Optional[DBUser] = Depends(get_current_user_optional),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    search: Optional[str] = Query(None),
    route_type_uuid: Optional[UUID] = Query(None),
    difficulty_uuid: Optional[UUID] = Query(None),
    location: Optional[str] = Query(None),
    ordering: Optional[str] = Query(None),
):
    return route_crud.get_public_routes(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        search=search,
        route_type_uuid=route_type_uuid,
        difficulty_uuid=difficulty_uuid,
        location=location,
        ordering=ordering,
    )


@router.get("/{route_id}", response_model=RouteOut)
def get_route(
    route_id: UUID,
    db: Session = Depends(get_db),
    current_user: Optional[DBUser] = Depends(get_current_user_optional)
):
    return route_crud.get_route_by_id(db, route_id, current_user)


@router.post("/", response_model=RouteOut)
def create_route(
    route_data: RouteCreate,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    return route_crud.create_route(db, route_data, creator=current_user)


@router.put("/{route_id}", response_model=RouteOut)
def update_route(
    route_id: UUID,
    route_data: RouteUpdate,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    return route_crud.update_route(db, route_id, route_data, current_user)


@router.delete("/{route_id}")
def delete_route(
    route_id: UUID,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    route_crud.delete_route(db, route_id, current_user)
    return {"detail": "Маршрут успешно удален"}



@router.get("/my/", response_model=List[RouteCardOut])
def get_my_routes(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000)
):
    return route_crud.get_routes_by_user(db, current_user, skip=skip, limit=limit)


@router.get("/user/{user_identifier}", response_model=List[RouteCardOut])
def get_public_routes_by_user(
    user_identifier: str,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    current_user: DBUser = Depends(get_current_user_optional)
):
    return route_crud.get_public_routes_by_user(db, user_identifier, skip, limit, current_user)


@router.post("/{route_id}/like", response_model=dict)
def like_route(
    route_id: UUID,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    route_crud.like_route(db, current_user, route_id)
    return {"detail": "Лайк добавлен"}

@router.delete("/{route_id}/like", response_model=dict)
def unlike_route(
    route_id: UUID,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    route_crud.unlike_route(db, current_user, route_id)
    return {"detail": "Лайк удалён"}


@router.post("/{route_id}/favorite", response_model=dict)
def add_to_favorites(
    route_id: UUID,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    route_crud.add_to_favorites(db, current_user, route_id)
    return {"detail": "Добавлено в избранное"}

@router.delete("/{route_id}/favorite", response_model=dict)
def remove_from_favorites(
    route_id: UUID,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    route_crud.remove_from_favorites(db, current_user, route_id)
    return {"detail": "Удалено из избранного"}


@router.get("/favorites/", response_model=List[RouteCardOut])
def get_favorites(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    return route_crud.get_favorites(db, current_user)


@router.patch("/{route_id}/to_draft", response_model=RouteOut)
def set_route_draft(
    route_id: UUID,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user),
):
    return route_crud.set_draft(db, route_id, current_user)


@router.patch("/{route_id}/publish", response_model=RouteOut)
def publish_route(
    route_id: UUID,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user),
):
    return route_crud.publish_route(db, route_id, current_user)


