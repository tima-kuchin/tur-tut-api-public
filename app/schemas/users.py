import datetime

from uuid import UUID
from typing import Optional
from pydantic import BaseModel, HttpUrl, EmailStr, constr, field_validator

from app.schemas.common import LoginStr, NameStr, Gender, UserRole

class UserBase(BaseModel):
    login: LoginStr
    email: EmailStr
    first_name: NameStr
    last_name: NameStr
    gender: Optional[Gender] = None
    age: Optional[int] = None
    profile_picture: Optional[HttpUrl] = HttpUrl("https://www.shutterstock.com/image-vector/blank-avatar-photo-place-holder-600nw-1095249842.jpg")
    description: Optional[str] = None

    @field_validator('login')
    def to_lowercase(cls, v):
        return v.lower()

class UserRegister(UserBase):
    password: constr(min_length=8)


class UserUpdate(BaseModel):
    first_name: Optional[NameStr] = None
    last_name: Optional[NameStr] = None
    gender: Optional[Gender] = None
    age: Optional[int] = None
    email: Optional[EmailStr] = None
    description: Optional[str] = None

class UserInfoPublic(BaseModel):
    login: str
    first_name: str | None
    last_name: str | None
    profile_picture: str | None
    description: Optional[str] | None

    @field_validator('login')
    def to_lowercase(cls, v):
        return v.lower()

    class Config:
        from_attributes = True

class AvatarUrlUpdate(BaseModel):
    profile_picture: str

class UserInfo(UserBase):
    uuid: UUID
    last_login: Optional[datetime.datetime] = None
    role: UserRole

    class Config:
        from_attributes = True