from enum import Enum

from pydantic import constr, BaseModel

LoginStr = constr(min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9\-_]+$')
NameStr = constr(min_length=1, max_length=50)

class Gender(str, Enum):
    male = "male"
    female = "female"

class UserRole(str, Enum):
    user = "user"
    moderator = "moderator"
    admin = "admin"

class ResponseMsg(BaseModel):
    message: str