from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status, Depends
from app.crud.users import get_user
from app.models.users import DBUser, UserRole
from app.core.security import hash_password, verify_password, check_password_strength


def delete_user_by_identifier(
    identifier: str,
    db: Session,
    current_user: DBUser
) -> None:
    user = get_user(db, identifier)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Администратор не может удалить себя"
        )
    if user.role == UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалять администратора"
        )
    try:
        db.delete(user)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении пользователя"
        )


def toggle_user_status(
    db: Session,
    current_user: DBUser,
    identifier: str,
    block_user: bool,
    block_reason: str | None = None,
) -> dict:
    user = get_user(db, identifier)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Администратор не может заблокировать себя"
        )
    if block_user and not block_reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Укажите причину блокировки"
        )
    user.is_blocked = block_user
    user.block_reason = block_reason if block_user else None
    user.block_date = datetime.now(timezone.utc) if block_user else None
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении статуса пользователя"
        )
    return {
        "login": user.login,
        "is_blocked": user.is_blocked,
        "block_reason": user.block_reason,
        "block_date": user.block_date,
    }

def change_user_role(
    identifier: str,
    new_role: UserRole,
    db: Session,
    current_user: DBUser
) -> dict:
    user = get_user(db, identifier)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Администратор не может сменить свой статус"
        )
    if user.role == new_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Пользователь уже имеет роль '{new_role.value}'"
        )
    old_role = user.role
    user.role = new_role
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при смене роли пользователя"
        )
    return {
        "login": user.login,
        "old_role": old_role.value,
        "new_role": user.role.value,
    }


def reset_password_for_user(
    db: Session,
    identifier: str,
    new_password: str,
    current_user: DBUser
) -> dict:
    user = get_user(db, identifier)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Для смены пароля, используй личный кабинет"
        )
    if user.role == UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нельзя менять пароль администратора"
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
            detail="Ошибка при смене пароля пользователя"
        )
    return {
        "login": user.login,
        "status": "Пароль успешно изменён"
    }


def get_users_list(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> list[DBUser]:
    """
    Получить список пользователей с пагинацией.
    :param db:
    :param skip: Количество пользователей, которое нужно пропустить (offset)
    :param limit: Максимальное количество пользователей в ответе
    """
    return db.query(DBUser).offset(skip).limit(limit).all()


def get_user_info(
    db: Session,
    identifier: str,
) -> DBUser:
    """
    Найти пользователя по логину или email.
    """
    user = get_user(db, identifier)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    return user