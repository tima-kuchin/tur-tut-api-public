from pydantic import BaseModel, constr, field_validator
from pydantic import EmailStr

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    @field_validator('email')
    def to_lowercase(cls, v):
        return v.lower()

class RestorePasswordRequest(BaseModel):
    token: str
    new_password: constr(min_length=8)

class ResetPasswordRequest(BaseModel):
    old_password: constr(min_length=8)
    new_password: constr(min_length=8)
