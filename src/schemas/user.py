from pydantic import EmailStr

from schemas.base import BaseOrmSchema
from utils.utils import ValidatePassword


class BaseUserSchema(BaseOrmSchema):
    name: str
    email: EmailStr


class GetUserSchema(BaseUserSchema):
    id: int


class CreateUserSchema(BaseUserSchema):
    password: ValidatePassword
