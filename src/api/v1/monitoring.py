from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse

from utils.monitoring import performance_monitor, health_checker, alert_manager
from utils.cache import cache_manager
from ws.connection import WebSocketConnectionManager

router = APIRouter(
    prefix="/monitoring", 
    tags=["System Monitoring"],
    responses={
        400: {"description": "Bad Request - Invalid parameters"},
        500: {"description": "Internal Server Error"},
        503: {"description": "Service Unavailable - System unhealthy"}
    }
)


@router.get(
    "/health",
    summary="System Health Check",
    description="""
    Комплексная проверка состояния системы.
    
    **Проверяемые компоненты:**
    - База данных
    - Redis кэш
    - WebSocket соединения
    - Общая производительность системы
    
    **Возможные статусы:**
    - healthy: Все системы работают нормально
    - degraded: Частичные проблемы
    - unhealthy: Критические проблемы
    
    **Использование:**
    - Для load balancer health checks
    - Мониторинг состояния системы
    - Автоматическое восстановление
    """,
    responses={
        200: {
            "description": "Система здорова",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "checks": {
                            "database": {"status": "healthy", "response_time": 0.05},
                            "redis": {"status": "healthy", "response_time": 0.01},
                            "websocket": {"status": "healthy", "active_connections": 10}
                        },
                        "timestamp": "2024-01-01T12:00:00Z"
                    }
                }
            }
        },
        503: {
            "description": "Система нездорова",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "error": "Database connection failed",
                        "timestamp": "2024-01-01T12:00:00Z"
                    }
                }
            }
        }
    }
)
async def health_check():
    """
    Комплексная проверка состояния системы.
    
    Returns:
        dict: Статус системы и результаты проверок
        
    Raises:
        HTTPException: Если система нездорова
    """
    try:
        # Запуск всех проверок здоровья
        health_results = await health_checker.run_checks()
        overall_status = health_checker.get_overall_status()
        
        return {
            "status": overall_status,
            "checks": health_results,
            "timestamp": performance_monitor.get_statistics()["timestamp"]
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": performance_monitor.get_statistics()["timestamp"]
            }
        )


@router.get(
    "/metrics",
    summary="Performance Metrics",
    description="""
    Получение метрик производительности системы.
    
    **Собираемые метрики:**
    - Время отклика API
    - Количество запросов
    - Частота ошибок
    - Использование памяти
    - Активные соединения
    
    **Использование:**
    - Мониторинг производительности
    - Анализ трендов
    - Выявление узких мест
    - Алертинг при проблемах
    """,
    responses={
        200: {
            "description": "Метрики получены",
            "content": {
                "application/json": {
                    "example": {
                        "statistics": {
                            "total_requests": 1000,
                            "average_response_time": 0.15,
                            "error_rate": 0.02,
                            "active_connections": 25
                        },
                        "metrics": {
                            "cpu_usage": 45.2,
                            "memory_usage": 67.8,
                            "disk_usage": 23.1
                        },
                        "cache_status": {
                            "redis_connected": True
                        }
                    }
                }
            }
        },
        500: {
            "description": "Ошибка получения метрик",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Failed to collect metrics"
                    }
                }
            }
        }
    }
)
async def get_metrics():
    """
    Получение метрик производительности.
    
    Returns:
        dict: Статистика и метрики системы
        
    Raises:
        HTTPException: При ошибке сбора метрик
    """
    try:
        stats = performance_monitor.get_statistics()
        metrics_summary = performance_monitor.get_metrics_summary()
        
        return {
            "statistics": stats,
            "metrics": metrics_summary,
            "cache_status": {
                "redis_connected": cache_manager._redis is not None
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )


@router.get(
    "/alerts",
    summary="Active Alerts",
    description="""
    Получение активных алертов системы.
    
    **Типы алертов:**
    - High error rate: Высокая частота ошибок
    - Slow response time: Медленное время отклика
    - High memory usage: Высокое использование памяти
    - Database issues: Проблемы с базой данных
    - Cache issues: Проблемы с кэшем
    
    **Уровни критичности:**
    - info: Информационные сообщения
    - warning: Предупреждения
    - critical: Критические проблемы
    """,
    responses={
        200: {
            "description": "Активные алерты получены",
            "content": {
                "application/json": {
                    "example": {
                        "alerts": [
                            {
                                "id": "alert_001",
                                "type": "high_error_rate",
                                "severity": "warning",
                                "message": "Error rate exceeded 5%",
                                "timestamp": "2024-01-01T12:00:00Z"
                            }
                        ],
                        "count": 1
                    }
                }
            }
        },
        500: {
            "description": "Ошибка получения алертов",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Failed to retrieve alerts"
                    }
                }
            }
        }
    }
)
async def get_alerts():
    """
    Получение активных алертов.
    
    Returns:
        dict: Список активных алертов и их количество
        
    Raises:
        HTTPException: При ошибке получения алертов
    """
    try:
        active_alerts = alert_manager.get_active_alerts()
        return {
            "alerts": active_alerts,
            "count": len(active_alerts)
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )


@router.get(
    "/connections",
    summary="WebSocket Connection Statistics",
    description="""
    Получение статистики WebSocket соединений.
    
    **Статистика включает:**
    - Общее количество активных соединений
    - Количество соединений по чатам
    - Время жизни соединений
    - Статистика отключений
    
    **Использование:**
    - Мониторинг нагрузки WebSocket
    - Анализ активности пользователей
    - Выявление проблем с соединениями
    """,
    responses={
        200: {
            "description": "Статистика соединений получена",
            "content": {
                "application/json": {
                    "example": {
                        "total_connections": 50,
                        "connections_by_chat": {
                            "1": 15,
                            "2": 20,
                            "3": 15
                        },
                        "average_connection_time": 1800,
                        "disconnections_last_hour": 5
                    }
                }
            }
        },
        500: {
            "description": "Ошибка получения статистики",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Failed to get connection stats"
                    }
                }
            }
        }
    }
)
async def get_connection_stats(connection_manager: WebSocketConnectionManager = Depends()):
    """
    Получение статистики WebSocket соединений.
    
    Args:
        connection_manager: Менеджер WebSocket соединений
        
    Returns:
        dict: Статистика соединений
        
    Raises:
        HTTPException: При ошибке получения статистики
    """
    try:
        stats = await connection_manager.get_connection_stats()
        return stats
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )


@router.get(
    "/cache/status",
    summary="Cache Status",
    description="""
    Проверка состояния кэша Redis.
    
    **Проверяемые параметры:**
    - Подключение к Redis
    - Тест записи/чтения
    - Размер пула соединений
    - Доступность операций
    
    **Использование:**
    - Диагностика проблем с кэшем
    - Мониторинг производительности Redis
    - Проверка конфигурации
    """,
    responses={
        200: {
            "description": "Статус кэша получен",
            "content": {
                "application/json": {
                    "example": {
                        "status": "connected",
                        "test_passed": True,
                        "pool_size": 10
                    }
                }
            }
        }
    }
)
async def get_cache_status():
    """
    Проверка состояния кэша.
    
    Returns:
        dict: Статус кэша и результаты тестов
    """
    try:
        # Тест подключения к кэшу
        test_key = "health_check_test"
        await cache_manager.set(test_key, "test", 10)
        test_value = await cache_manager.get(test_key)
        await cache_manager.delete(test_key)
        
        return {
            "status": "connected" if cache_manager._redis else "disconnected",
            "test_passed": test_value == "test",
            "pool_size": cache_manager._connection_pool.max_connections if cache_manager._connection_pool else 0
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.post(
    "/cache/clear",
    summary="Clear Cache",
    description="""
    Очистка всего содержимого кэша Redis.
    
    **Внимание:** Эта операция удаляет все данные из кэша.
    Используйте с осторожностью в продакшене.
    
    **Применение:**
    - Очистка устаревших данных
    - Сброс проблемного состояния кэша
    - Тестирование и отладка
    """,
    responses={
        200: {
            "description": "Кэш успешно очищен",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Cache cleared successfully"
                    }
                }
            }
        },
        503: {
            "description": "Кэш недоступен",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Cache not available"
                    }
                }
            }
        },
        500: {
            "description": "Ошибка очистки кэша",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Failed to clear cache"
                    }
                }
            }
        }
    }
)
async def clear_cache():
    """
    Очистка всего содержимого кэша.
    
    Returns:
        dict: Результат операции очистки
        
    Raises:
        HTTPException: Если кэш недоступен или произошла ошибка
    """
    try:
        if cache_manager._redis:
            await cache_manager._redis.flushdb()
            return {"message": "Cache cleared successfully"}
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"error": "Cache not available"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )


@router.get(
    "/performance/summary",
    summary="Performance Summary",
    description="""
    Получение сводки производительности за последний час.
    
    **Рассчитываемые показатели:**
    - Общий балл производительности (0-100)
    - Частота ошибок
    - Среднее время отклика
    - Общее количество запросов
    - Активные соединения
    
    **Алгоритм оценки:**
    - Оценка ошибок: -10 баллов за каждый 1% ошибок
    - Оценка времени отклика: -20 баллов за каждую секунду
    - Итоговый балл: среднее арифметическое
    
    **Интерпретация баллов:**
    - 90-100: Отличная производительность
    - 70-89: Хорошая производительность
    - 50-69: Удовлетворительная производительность
    - 0-49: Проблемы с производительностью
    """,
    responses={
        200: {
            "description": "Сводка производительности получена",
            "content": {
                "application/json": {
                    "example": {
                        "performance_score": 85.5,
                        "error_rate": 0.02,
                        "average_response_time": 0.15,
                        "total_requests": 1000,
                        "active_connections": 25,
                        "metrics_summary": {
                            "cpu_usage": 45.2,
                            "memory_usage": 67.8
                        }
                    }
                }
            }
        },
        500: {
            "description": "Ошибка получения сводки",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Failed to get performance summary"
                    }
                }
            }
        }
    }
)
async def get_performance_summary():
    """
    Получение сводки производительности.
    
    Returns:
        dict: Сводка производительности с баллом и метриками
        
    Raises:
        HTTPException: При ошибке расчета сводки
    """
    try:
        stats = performance_monitor.get_statistics()
        metrics = performance_monitor.get_metrics_summary()
        
        # Расчет балла производительности (0-100)
        error_rate = stats.get("error_rate", 0)
        avg_response_time = stats.get("average_response_time", 0)
        
        # Простой алгоритм оценки
        error_score = max(0, 100 - error_rate * 10)  # -10 баллов за каждый 1% ошибок
        response_score = max(0, 100 - avg_response_time * 20)  # -20 баллов за каждую секунду
        performance_score = (error_score + response_score) / 2
        
        return {
            "performance_score": round(performance_score, 2),
            "error_rate": error_rate,
            "average_response_time": avg_response_time,
            "total_requests": stats.get("total_requests", 0),
            "active_connections": stats.get("active_connections", 0),
            "metrics_summary": metrics
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        ) 