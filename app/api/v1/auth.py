from fastapi import APIRouter, Depends, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.security import get_current_user
from app.models.users import DBUser
from app.crud import auth
from app.schemas.auth import TokenResponse, ForgotPasswordRequest, RestorePasswordRequest, ResetPasswordRequest
from app.schemas.common import ResponseMsg
from app.schemas.users import UserInfo, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post(
    "/register",
    response_model=UserInfo,
    description="Регистрация нового пользователя. Требует уникальные логин и email."
)
def register(
        user_data: UserRegister,
        db: Session = Depends(get_db)
) -> UserInfo:
    """
    Зарегистрировать нового пользователя.
    """
    user = auth.register_user(db, user_data)
    return UserInfo.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    description="Авторизация пользователя по логину или email и паролю. Возвращает access и refresh токены."
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Войти в систему, получить access и refresh токены.
    """
    tokens = auth.authenticate_user(db, form_data.username, form_data.password)
    return TokenResponse.model_validate(tokens)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    description="Обновить access токен по refresh токену, переданному в заголовке X-Refresh-Token."
)
def refresh_token(
    db: Session = Depends(get_db),
    refresh_token: str = Header(
        ...,
        alias="X-Refresh-Token",
        description="Refresh Token в заголовке"
    ),

) -> TokenResponse:
    """
    Получить новый access токен по refresh токену.
    """
    new_access = auth.refresh_access_token(refresh_token, db)
    return TokenResponse.model_validate(new_access)


@router.post(
    "/forgot_password",
    response_model=ResponseMsg,
    description="Запросить восстановление пароля. Если email зарегистрирован, на него будет отправлена инструкция для сброса пароля."
)
def forgot_password(
        data: ForgotPasswordRequest,
        db: Session = Depends(get_db)
) -> ResponseMsg:
    """
    Запросить отправку письма для восстановления пароля.
    """
    auth.send_reset_email(db, str(data.email))
    return ResponseMsg.model_validate({"message": "Инструкция по восстановлению пароля отправлена на email, если он зарегистрирован"})


@router.post(
    "/restore_password",
    response_model=ResponseMsg,
    description="Установить новый пароль по токену восстановления из email."
)
def restore_password(
        data: RestorePasswordRequest,
        db: Session = Depends(get_db)
) -> ResponseMsg:
    """
    Восстановить пароль по токену из email.
    """
    auth.restore_password_from_email(db, data.token, data.new_password)
    return ResponseMsg.model_validate({"message": "Пароль успешно обновлён"})


@router.post(
    "/reset_password",
    response_model=ResponseMsg,
    description="Изменить пароль в профиле. Требуется передать старый и новый пароли, пользователь должен быть авторизован."
)
def reset_password(
    data: ResetPasswordRequest ,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseMsg:
    """
    Сменить пароль в профиле (требуется старый и новый пароль).
    """
    auth.reset_user_password(db, current_user, data.old_password, data.new_password)
    return ResponseMsg.model_validate({"message": "Пароль успешно изменён"})
