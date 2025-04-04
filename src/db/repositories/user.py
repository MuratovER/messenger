from sqlalchemy import select

from db.models.user import User
from db.repositories.base import BaseDatabaseRepository
from schemas.user import CreateUserSchema


class UserRepository(BaseDatabaseRepository):
    async def get_user_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        query_result = await self._session.execute(query)
        return query_result.scalar_one_or_none()

    async def create_user(self, user_data: CreateUserSchema) -> User:
        user = await User.create_user_with_hashed_password(create_data=user_data)
        self._session.add(user)
        await self._session.flush()
        await self._session.commit()
        return user

    async def get_user_by_id(self, user_id: int) -> User | None:
        return await self._session.get(User, user_id)
