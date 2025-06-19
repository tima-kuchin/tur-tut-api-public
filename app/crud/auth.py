from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException, status
from app.models.users import DBUser
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    generate_reset_token,
    verify_reset_token
)
from app.crud.users import get_user, ensure_email_unique, ensure_login_unique
from app.core.security import check_password_strength
from app.schemas.users import UserRegister


def register_user(
        db: Session,
        user_data: UserRegister
) -> DBUser:
    ensure_email_unique(db, str(user_data.email))
    ensure_login_unique(db, str(user_data.login))
    check_password_strength(user_data.password)
    new_user = DBUser(
        login=user_data.login,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        gender=user_data.gender,
        age=user_data.age,
        profile_picture=str(user_data.profile_picture) if user_data.profile_picture else None
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с такими данными уже существует."
        )
    db.refresh(new_user)
    return new_user

def authenticate_user(
        db: Session,
        login: str,
        password: str
) -> dict:
    try:
        user = get_user(db, login)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный логин или пароль"
            )
        if user.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Учетная запись заблокирована"
            )
        user.last_login = datetime.now(timezone.utc)
        db.commit()
        return {
            "access_token": create_access_token(subject=user.login, role=user.role.value),
            "refresh_token": create_refresh_token(subject=user.login, role=user.role.value),
        }
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка сервера при авторизации"
        )



def refresh_access_token(
        refresh_token: str,
        db: Session
) -> dict:
    login, _ = verify_refresh_token(refresh_token)
    user = get_user(db, login)
    if not user or user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недействительный или заблокированный пользователь"
        )
    return {
        "access_token": create_access_token(subject=user.login, role=user.role.value),
        "refresh_token": create_refresh_token(subject=user.login, role=user.role.value),
    }


def send_reset_email(
        db: Session,
        email: str
) -> None:
    user = db.query(DBUser).filter(DBUser.email == email).first()
    if not user:
        return
    token = generate_reset_token(user.login)
    # TODO: Полная реализация будет сделана при выходе в "прод" и аренды smtp-сервера
    print(f"[DEBUG] Password reset link for {user.email}: https://frontend/reset-password?token={token}")


def restore_password_from_email(
        db: Session,
        token: str,
        new_password: str
) -> None:
    login = verify_reset_token(token)
    user = db.query(DBUser).filter(DBUser.login == login).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    restore_user_password(db, user, new_password)


def restore_user_password(
        db: Session,
        user: DBUser,
        new_password: str
) -> None:
    if verify_password(new_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Новый пароль не должен совпадать со старым"
        )
    check_password_strength(new_password)
    user.hashed_password = hash_password(new_password)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка сервера при сохранении нового пароля"
        )


def reset_user_password(
    db: Session,
    user: DBUser,
    old_password: str,
    new_password: str
) -> None:
    if not verify_password(old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Старый пароль введён неверно"
        )
    if verify_password(new_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Новый пароль не должен совпадать со старым"
        )
    check_password_strength(new_password)
    user.hashed_password = hash_password(new_password)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка сервера при сохранении нового пароля"
        )