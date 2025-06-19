import bcrypt
import jwt

from datetime import datetime, timedelta, timezone
from app.core.config import settings
from fastapi import HTTPException, status
from jwt import ExpiredSignatureError, InvalidTokenError

from app.schemas.common import UserRole


def hash_password(password: str) -> str:
    """
    Хеширование пароля пользователя с помощью bcrypt.
    Возвращает строку с солью и хешем.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет совпадение пароля пользователя с хешем из БД.
    """
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def verify_access_token(token: str) -> tuple[str, str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный тип токена")
        login = payload.get("sub")
        role = payload.get("role")
        if not login or not role:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Некорректный payload токена")
        return login, role

    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Срок действия токена истёк")
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен")


def create_access_token(
    *, subject: str, role: str, expires_delta: timedelta = settings.token_expiration
) -> str:
    """
    Генерирует access JWT-токен для пользователя.
    subject — уникальный идентификатор пользователя (сейчас это login).
    Срок действия задается expires_delta (по умолчанию — из настроек).
    """
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": subject, "role": role, "exp": expire, "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(*, subject: str, role: str) -> str:
    """
    Генерирует refresh JWT-токен для пользователя.
    Стандартный срок жизни — 7 дней.
    """
    expire = datetime.now(timezone.utc) + settings.refresh_token_expiration
    to_encode = {"sub": subject, "role": role, "exp": expire, "type": "refresh"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_refresh_token(token: str) -> tuple[str, str]:
    """
    Валидирует refresh токен, возвращает subject (login).
    Бросает HTTPException при ошибке валидации или истечении срока.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный тип токена")

        role = payload.get("role")
        if role not in [r.value for r in UserRole]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недопустимая роль в токене")

        return payload["sub"], role

    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Срок действия refresh токена истёк")
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный refresh токен")

def generate_reset_token(subject: str, expires_minutes: int = 30) -> str:
    """
    Генерирует одноразовый JWT-токен для восстановления пароля.
    По умолчанию срок жизни — 30 минут.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode = {"sub": subject, "exp": expire, "type": "reset"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_reset_token(token: str) -> str:
    """
    Валидирует токен восстановления пароля, возвращает subject (login).
    Бросает HTTPException при ошибке валидации или истечении срока.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "reset":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный тип токена восстановления")
        return payload["sub"]
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Срок действия токена восстановления истёк")
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен восстановления")


def check_password_strength(password: str) -> None:
    """
    Проверяет сложность пароля: минимум 8 символов, буквы и цифры.
    Raises:
        HTTPException: Если пароль слишком простой.
    """
    if len(password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пароль слишком короткий")
    if password.isdigit() or password.isalpha():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пароль должен содержать буквы и цифры")