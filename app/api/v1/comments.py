from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.security import get_current_user, get_current_user_optional
from app.schemas.comments import CommentCreate, CommentOut
from app.crud import comments as comments_crud
from app.models.users import DBUser
from app.schemas.common import ResponseMsg

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/{comment_id}/like", response_model=ResponseMsg)
def like_comment(
    comment_id: UUID,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    comments_crud.like_comment(db, comment_id, current_user)
    return {"message": "Лайк добавлен"}


@router.delete("/{comment_id}/like", response_model=ResponseMsg)
def unlike_comment(
    comment_id: UUID,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    comments_crud.unlike_comment(db, comment_id, current_user)
    return {"message": "Лайк удалён"}


@router.delete("/{comment_id}", response_model=ResponseMsg)
def delete_comment(
    comment_id: UUID,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    comments_crud.delete_comment(db, comment_id, current_user)
    return {"message": "Комментарий удалён"}


@router.get("/{target_type}/{target_uuid}", response_model=List[CommentOut])
def get_comments(
    target_type: str,
    target_uuid: UUID,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user_optional)
):
    return comments_crud.get_comments(db, target_type, target_uuid, current_user)

@router.post("/{target_type}/{target_uuid}", response_model=CommentOut)
def create_comment(
    target_type: str,
    target_uuid: UUID,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    return comments_crud.create_comment(db, target_type, target_uuid, comment, current_user)






