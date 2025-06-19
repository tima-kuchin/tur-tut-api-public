import os
import shutil, uuid
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from typing import List
from app.core.config import settings
from app.models.users import DBUser
from app.schemas.users import UserUpdate


def get_user(
        db: Session,
        identifier: str
) -> DBUser | None:
    return db.query(DBUser).filter(or_(DBUser.login == identifier, DBUser.email == identifier)).first()


def ensure_login_unique(
        db: Session,
        login: str
) -> None:
    if db.query(DBUser).filter(DBUser.login == login).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Логин уже используется другим пользователем"
        )


def ensure_email_unique(
        db: Session,
        email: str
) -> None:
    if db.query(DBUser).filter(DBUser.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email уже используется другим пользователем"
        )


def get_users_list(
        db: Session,
        skip: int = 0,
        limit: int = 100
) -> List[DBUser]:
    """
    Получить публичный список пользователей с пагинацией.
    """
    return db.query(DBUser).offset(skip).limit(limit).all()


def update_user(
        db: Session,
        user: DBUser,
        update_data: UserUpdate
) -> DBUser:
    """
    Обновить свой профиль (без login/роли).
    """
    data = update_data.model_dump(exclude_unset=True)
    data.pop("login", None)
    if "email" in data and data["email"] != user.email:
        ensure_email_unique(db, data["email"])
        user.email = data["email"]
    for key, value in data.items():
        if key != "email":
            setattr(user, key, value)
    try:
        db.commit()
        db.refresh(user)
        return user
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении профиля"
        )


def update_avatar(
    db: Session,
    user: DBUser,
    file
) -> DBUser:
    upload_dir = settings.AVATAR_UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".gif"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недопустимый формат файла")
    filename = f"{user.login}_{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(upload_dir, filename)
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        user.profile_picture = f"{settings.BASE_STATIC_URL}/avatars/{filename}"
        db.commit()
        db.refresh(user)
        return user
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при загрузке аватара: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка при загрузке аватара: {str(e)}"
        )


def update_avatar_url(
    db: Session,
    user: DBUser,
    new_profile_picture: str
) -> DBUser:
    try:
        user.profile_picture = new_profile_picture
        db.commit()
        db.refresh(user)
        return user
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении аватара: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка при обновлении аватара: {str(e)}"
        )