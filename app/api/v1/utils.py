from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.tag import RouteTag
from app.models.dictionaries import RouteType, DifficultyType
from app.models.target_types import TargetType

router = APIRouter(prefix="/utils", tags=["utils"])

@router.get("/route_types")
def get_route_types(db: Session = Depends(get_db)):
    return db.query(RouteType).all()

@router.get("/difficulty_types")
def get_difficulty_types(db: Session = Depends(get_db)):
    return db.query(DifficultyType).all()

@router.get("/target_types")
def get_target_types(db: Session = Depends(get_db)):
    return db.query(TargetType).all()

@router.get("/route_tags")
def get_target_types(db: Session = Depends(get_db)):
    return db.query(RouteTag).all()