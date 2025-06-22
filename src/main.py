import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from api.router import api_router
from api.v1.messages import router as ws_router
from core.config import settings
from db.init_data.init_data import init_data
from db.session import health_check


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling exceptions and errors."""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Unhandled exception: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = asyncio.get_event_loop().time()
        
        response = await call_next(request)
        
        process_time = asyncio.get_event_loop().time() - start_time
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s"
        )
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with improved error handling."""
    logger.info("🚀 Starting Messenger application...")
    
    # Initialize database if needed
    if settings().ENVIRONMENT == "showroom":
        logger.info("🔄 Запуск инициализации базы данных...")
        try:
            await init_data()
            logger.success("✅ Инициализация базы данных завершена")
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации базы данных: {e}")
            raise
    
    # Health check
    try:
        db_healthy = await health_check()
        if not db_healthy:
            logger.error("❌ Database health check failed")
            raise Exception("Database connection failed")
        logger.success("✅ Database health check passed")
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise
    
    logger.success("✅ Messenger application started successfully")
    
    yield
    
    logger.info("🛑 Shutting down Messenger application...")


app = FastAPI(
    title="Messenger",
    description="A real-time messaging application with WebSocket support",
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/swagger",
    lifespan=lifespan,
)

# Add middleware in order of execution
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Security middleware
if settings().is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings().cors_allow_origins
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings().cors_allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)

app.add_middleware(
    SessionMiddleware, 
    secret_key=settings().SESSION_MIDDLEWARE_SECRET,
    max_age=3600,  # 1 hour
    same_site="lax",
    https_only=settings().is_production,
)

# Include routers
app.include_router(api_router)
app.include_router(ws_router)


@app.get("/health", tags=["Health"])
async def health_endpoint():
    """Health check endpoint."""
    try:
        db_healthy = await health_check()
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "database": "connected" if db_healthy else "disconnected",
            "environment": settings().ENVIRONMENT,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "environment": settings().ENVIRONMENT,
            }
        )


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Messenger API",
        "version": "1.0.0",
        "docs": "/api/swagger",
        "health": "/health"
    }


# Global exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )
