import jwt
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Sequence
from app.crud.users import get_user
from app.db.session import get_db
from app.models.users import DBUser, UserRole
from app.core.security import verify_access_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> DBUser:
    login, role = verify_access_token(token)

    user = get_user(db, login)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
    if user.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Пользователь заблокирован")

    return user


def get_current_admin_user(
    current_user: DBUser = Depends(get_current_user)
) -> DBUser:
    if current_user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ разрешён только администраторам")
    return current_user


def get_current_moderator_user(
    current_user: DBUser = Depends(get_current_user)
) -> DBUser:
    if current_user.role.value not in ("moderator", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Требуется роль модератора или выше")
    return current_user


def get_current_user_optional(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> DBUser | None:
    """
    Возвращает текущего пользователя, если токен валиден.
    Если токена нет или он невалиден/истёк — возвращает None.
    """
    if not token:
        return None
    try:
        login, _ = verify_access_token(token)
    except HTTPException as e:
        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            return None
        raise
    return get_user(db, login)