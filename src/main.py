from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from api.router import api_router
from api.v1.messages import router as ws_router
from core.config import settings
from db.init_data.init_data import init_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings().ENVIRONMENT == "showroom":
        logger.info("🔄 Запуск инициализации базы данных...")
        try:
            await init_data()
            logger.success("✅ Инициализация базы данных завершена")
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации базы данных: {e}")
            raise
    yield


app = FastAPI(
    title="Messenger",
    openapi_url="/api/openapi.json",
    docs_url="/api/swagger",
    lifespan=lifespan,
)


app.include_router(api_router)
app.include_router(ws_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings().cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=settings().SESSION_MIDDLEWARE_SECRET)
