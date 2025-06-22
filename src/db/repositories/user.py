from sqlalchemy import select, or_
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

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

    async def update(self, user_id: int, update_data: dict) -> User:
        """
        Обновление данных пользователя.
        
        Args:
            user_id: ID пользователя
            update_data: Данные для обновления
            
        Returns:
            User: Обновленный пользователь
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def search_users(
        self, 
        query: str, 
        current_user_id: int, 
        params: Params
    ) -> Page[User]:
        """
        Поиск пользователей по имени или email.
        
        Args:
            query: Поисковый запрос
            current_user_id: ID текущего пользователя (исключается из результатов)
            params: Параметры пагинации
            
        Returns:
            Page[User]: Пагинированные результаты поиска
        """
        search_query = f"%{query}%"
        sql_query = select(User).where(
            or_(
                User.name.ilike(search_query),
                User.email.ilike(search_query)
            ),
            User.id != current_user_id
        ).order_by(User.name)
        
        return await paginate(self._session, sql_query, params)
