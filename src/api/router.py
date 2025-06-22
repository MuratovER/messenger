from fastapi import APIRouter
from fastapi_pagination import add_pagination

from api.v1.auth import router as auth_router
from api.v1.chat import router as chat_router
from api.v1.messages import router as messages_router
from api.v1.monitoring import router as monitoring_router
from api.v1.users import router as users_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(auth_router)
v1_router.include_router(chat_router)
v1_router.include_router(messages_router)
v1_router.include_router(monitoring_router)
v1_router.include_router(users_router)

add_pagination(v1_router)

api_router = APIRouter(prefix="/api")
api_router.include_router(v1_router)
