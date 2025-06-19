from typing import Optional
from pydantic import BaseModel, constr, field_validator

from app.models.users import UserRole

class SetUserRoleRequest(BaseModel):
    login: str
    role: UserRole

    @field_validator('login')
    def to_lowercase(cls, v):
        return v.lower()

class ToggleUserStatusRequest(BaseModel):
    login: str
    block_user: bool
    block_reason: Optional[str] = None

    @field_validator('login')
    def to_lowercase(cls, v):
        return v.lower()

class ResetUserPasswordRequest(BaseModel):
    login: str
    new_password: constr(min_length=8)

    @field_validator('login')
    def to_lowercase(cls, v):
        return v.lower()
