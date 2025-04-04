from db.models.user import User
from tests.factories.base import BaseFactory
from tests.factories.fakers import UniqueStringFaker


class BaseUserFactory(BaseFactory):
    class Meta:
        model = User

    name = UniqueStringFaker("name")
    email = UniqueStringFaker("email")


class UserFactory(BaseUserFactory):
    hashed_password = UniqueStringFaker("pystr")
