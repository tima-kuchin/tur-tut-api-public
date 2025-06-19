from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.users import DBUser

from app.crud import admin as admin_crud
from app.dependencies.security import get_current_admin_user
from app.schemas.admin import ToggleUserStatusRequest, SetUserRoleRequest, ResetUserPasswordRequest
from app.schemas.common import ResponseMsg
from app.schemas.users import UserInfo

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post(
    "/toggle_user_active",
    response_model=ResponseMsg,
    description="Включение или блокировка пользователя по логину или email. "
                "При блокировке обязательно указать причину."
)
def toggle_user_active(
    data: ToggleUserStatusRequest,
    current_user: DBUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Включить или заблокировать пользователя (по логину или email).
    При блокировке требуется указать причину.
    Доступно только администратору.
    """
    result = admin_crud.toggle_user_status(
        identifier=data.login,
        block_user=data.block_user,
        block_reason=data.block_reason,
        db=db,
        current_user=current_user
    )
    status = "отключена" if result["is_blocked"] else "включена"
    return {"message": f"Учетная запись пользователя '{data.login}' {status}."}


@router.post(
    "/set_user_role",
    response_model=ResponseMsg,
    description="Изменение роли пользователя (по логину или email). Нельзя установить текущую роль повторно."
)
def set_user_role(
    data: SetUserRoleRequest,
    current_user: DBUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Изменить роль пользователя (по логину или email).
    Повторное назначение той же роли запрещено.
    Доступно только администратору.
    """
    result = admin_crud.change_user_role(
        identifier=data.login,
        new_role=data.role,
        db=db,
        current_user=current_user
    )
    return {"message": f"Роль пользователя '{result['login']}' изменена с '{result['old_role']}' на '{result['new_role']}'."}


@router.post(
    "/reset_user_password",
    response_model=ResponseMsg,
    description="Сброс пароля пользователю (по логину или email). Новый пароль не должен совпадать со старым. "
                "Администраторам запрещено менять пароли других админов."
)
def reset_user_password(
    data: ResetUserPasswordRequest,
    current_user: DBUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Сбросить пароль пользователя (по логину или email).
    Новый пароль не должен совпадать с текущим.
    Администраторы не могут менять пароли другим администраторам.
    """
    result = admin_crud.reset_password_for_user(
        db=db,
        identifier=data.login,
        new_password=data.new_password,
        current_user=current_user
    )
    return {"message": f"Пароль пользователя '{result['login']}' успешно изменён."}


@router.delete(
    "/delete_user",
    response_model=ResponseMsg,
    description="Удалить пользователя по логину или email. Нельзя удалять учетную запись администратора."
)
def delete_user(
    identifier: str,
    current_user: DBUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Удалить пользователя по логину или email.
    Удаление учетной записи администратора запрещено.
    Доступно только администратору.
    """
    admin_crud.delete_user_by_identifier(
        identifier=identifier,
        db=db,
        current_user=current_user
    )
    return {"message": f"Пользователь '{identifier}' успешно удалён."}


@router.get(
    "/get_user_info",
    response_model=UserInfo,
    description="Получить подробную информацию о пользователе по логину или email."
)
def get_user_info(
    identifier: str,
    current_user: DBUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> UserInfo:
    """
    Получить полную информацию о пользователе по логину или email.
    Доступно только администратору.
    """
    user = admin_crud.get_user_info(db, identifier)
    return UserInfo.model_validate(user)


@router.get(
    "/get_users_list",
    response_model=List[UserInfo],
    description="Получить список всех пользователей с пагинацией. "
                "Параметры skip и limit позволяют управлять страницами."
)
def get_users_list(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_admin_user),
    skip: int = 0,
    limit: int = 100
) -> list[UserInfo]:
    """
    Получить список всех пользователей с пагинацией.
    Пример: /admin/get_users_list?skip=0&limit=50
    """
    users = admin_crud.get_users_list(db, skip=skip, limit=limit)
    return [UserInfo.model_validate(u) for u in users]