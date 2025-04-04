from schemas.base import BaseOrmSchema
from utils.utils import pwd_context


class LoginSchema(BaseOrmSchema):
    email: str
    password: str

    def hashed_password(self) -> str:
        return pwd_context.hash(self.password)


class TokenSchema(BaseOrmSchema):
    access_token: str
    refresh_token: str
