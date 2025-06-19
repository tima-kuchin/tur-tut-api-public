from typing import List
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.security import get_current_user
from app.models.users import DBUser
from app.crud import users as users_crud
from app.schemas.users import UserInfo, UserUpdate, UserInfoPublic, AvatarUrlUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserInfo, description="Получить свой профиль (детальная информация)")
def get_self_info(
        current_user: DBUser = Depends(get_current_user)
) -> UserInfo:
    return UserInfo.model_validate(current_user)


@router.put("/me", response_model=UserInfo, description="Изменить свой профиль (кроме логина и роли)")
def edit_self_info(
    user_update: UserUpdate,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserInfo:
    user = users_crud.update_user(db, current_user, user_update)
    return UserInfo.model_validate(user)


@router.post("/me/avatar_file", response_model=UserInfo, description="Загрузить или обновить аватар профиля")
def upload_avatar(
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
) -> UserInfo:
    """
    Загрузить/заменить фото профиля.
    """
    user = users_crud.update_avatar(db, current_user, file)
    return UserInfo.model_validate(user)

@router.post("/me/avatar", response_model=UserInfo, description="Установить ссылку на аватар профиля")
def set_avatar_url(
    data: AvatarUrlUpdate,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserInfo:
    """
    Установить/заменить фото профиля по ссылке.
    """
    user = users_crud.update_avatar_url(db, current_user, str(data.profile_picture))
    return UserInfo.model_validate(user)

@router.get("/{identifier}", response_model=UserInfoPublic, description="Публичный профиль пользователя по логину или email")
def get_user_info(
    identifier: str,
    db: Session = Depends(get_db)
) -> UserInfoPublic:
    user = users_crud.get_user(db, identifier)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return UserInfoPublic.model_validate(user)


@router.get("/", response_model=List[UserInfoPublic], description="Публичный список пользователей с пагинацией")
def get_users_list(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Сколько пользователей пропустить"),
    limit: int = Query(50, ge=1, le=100, description="Сколько пользователей вернуть"),
) -> List[UserInfoPublic]:
    users = users_crud.get_users_list(db, skip=skip, limit=limit)
    return [UserInfoPublic.model_validate(u) for u in users]
