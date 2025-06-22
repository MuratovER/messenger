from typing import Optional

from fastapi import HTTPException, status
from fastapi_pagination import Page, Params

from db.models.user import User
from db.repositories.user import UserRepository
from schemas.user import UpdateUserSchema


class UserService:
    def __init__(self, user_repository: UserRepository = None):
        self.user_repository = user_repository or UserRepository()

    async def get_user_by_id(self, user_id: int) -> User:
        """
        Получение пользователя по ID.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            User: Объект пользователя
            
        Raises:
            HTTPException: Если пользователь не найден
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    async def update_user(self, user_id: int, user_data: UpdateUserSchema) -> User:
        """
        Обновление данных пользователя.
        
        Args:
            user_id: ID пользователя
            user_data: Данные для обновления
            
        Returns:
            User: Обновленный пользователь
            
        Raises:
            HTTPException: Если email уже существует или данные неверны
        """
        # Проверка существования пользователя
        user = await self.get_user_by_id(user_id)
        
        # Проверка уникальности email если он обновляется
        if user_data.email and user_data.email != user.email:
            existing_user = await self.user_repository.get_by_email(user_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
        
        # Обновление данных
        update_data = user_data.dict(exclude_unset=True)
        if update_data:
            user = await self.user_repository.update(user_id, update_data)
        
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
            current_user_id: ID текущего пользователя
            params: Параметры пагинации
            
        Returns:
            Page[User]: Пагинированные результаты поиска
        """
        return await self.user_repository.search_users(
            query=query,
            current_user_id=current_user_id,
            params=params
        ) 