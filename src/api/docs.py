"""
Документация API для Messenger приложения.

Этот модуль содержит настройки OpenAPI документации,
включая общую информацию, теги и примеры использования.
"""

from fastapi.openapi.utils import get_openapi

# Общая информация о API
API_TITLE = "Messenger API"
API_VERSION = "1.0.0"
API_DESCRIPTION = """
# Messenger API

Современное API для мессенджера с поддержкой реального времени.

## Основные возможности

### 🔐 Аутентификация
- Регистрация и вход пользователей
- JWT токены с refresh механизмом
- Безопасное хранение паролей

### 💬 Управление чатами
- Создание групповых и приватных чатов
- Добавление участников
- История сообщений с пагинацией

### 📱 Реальное время
- WebSocket соединения для мгновенных сообщений
- Уведомления о статусе "печатает"
- Индикация прочтения сообщений

### 👥 Управление пользователями
- Профили пользователей
- Поиск пользователей
- Обновление профилей

### 📊 Мониторинг
- Проверка состояния системы
- Метрики производительности
- Алерты и уведомления

## Аутентификация

API использует JWT токены для аутентификации. Для доступа к защищенным эндпоинтам:

1. Зарегистрируйтесь через `/api/v1/auth/sign-up`
2. Войдите через `/api/v1/auth/login`
3. Используйте полученный `access_token` в заголовке `Authorization: Bearer <token>`

## WebSocket соединения

Для реального времени используйте WebSocket эндпоинт:
```
ws://your-domain/api/v1/messages/ws/{chat_id}?token={access_token}
```

## Пагинация

API поддерживает пагинацию для списков. Используйте параметры:
- `page`: Номер страницы (по умолчанию 1)
- `size`: Размер страницы (по умолчанию 20)

## Коды ошибок

- `400` - Неверный запрос
- `401` - Не авторизован
- `403` - Доступ запрещен
- `404` - Не найдено
- `422` - Ошибка валидации
- `500` - Внутренняя ошибка сервера
- `503` - Сервис недоступен

## Примеры использования

### Создание чата
```bash
curl -X POST "http://localhost:8000/api/v1/chats" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Team Chat",
    "participants": [1, 2, 3]
  }'
```

### Отправка сообщения через WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/messages/ws/1?token=YOUR_TOKEN');
ws.send(JSON.stringify({
  type: 'message',
  text: 'Hello everyone!'
}));
```

## Разработка

API построен на FastAPI с использованием:
- SQLAlchemy для работы с базой данных
- Redis для кэширования
- WebSocket для реального времени
- JWT для аутентификации
- Pydantic для валидации данных
"""

# Настройки тегов для группировки эндпоинтов
TAGS_METADATA = [
    {
        "name": "Authentication",
        "description": "Операции аутентификации и авторизации пользователей.",
        "externalDocs": {
            "description": "Документация по безопасности",
            "url": "https://docs.example.com/security",
        },
    },
    {
        "name": "Chat Management",
        "description": "Управление чатами, создание и получение истории сообщений.",
        "externalDocs": {
            "description": "Руководство по чатам",
            "url": "https://docs.example.com/chat",
        },
    },
    {
        "name": "Real-time Messaging",
        "description": "WebSocket соединения для обмена сообщениями в реальном времени.",
        "externalDocs": {
            "description": "WebSocket документация",
            "url": "https://docs.example.com/websocket",
        },
    },
    {
        "name": "User Management",
        "description": "Управление профилями пользователей и поиск.",
        "externalDocs": {
            "description": "Руководство пользователя",
            "url": "https://docs.example.com/users",
        },
    },
    {
        "name": "System Monitoring",
        "description": "Мониторинг состояния системы, метрики и алерты.",
        "externalDocs": {
            "description": "Мониторинг системы",
            "url": "https://docs.example.com/monitoring",
        },
    },
]

# Настройки серверов
SERVERS = [
    {
        "url": "http://localhost:8000",
        "description": "Локальная среда разработки"
    },
    {
        "url": "https://api.messenger.example.com",
        "description": "Продакшн сервер"
    },
    {
        "url": "https://staging.messenger.example.com",
        "description": "Стейджинг сервер"
    }
]

# Настройки безопасности
SECURITY_SCHEMES = {
    "bearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT токен для аутентификации. Получите токен через эндпоинт /api/v1/auth/login"
    }
}

# Глобальные ответы
GLOBAL_RESPONSES = {
    "400": {
        "description": "Неверный запрос",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Invalid request data"
                }
            }
        }
    },
    "401": {
        "description": "Не авторизован",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Not authenticated"
                }
            }
        }
    },
    "403": {
        "description": "Доступ запрещен",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Access denied"
                }
            }
        }
    },
    "404": {
        "description": "Не найдено",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Resource not found"
                }
            }
        }
    },
    "422": {
        "description": "Ошибка валидации",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {
                            "loc": ["body", "field_name"],
                            "msg": "field required",
                            "type": "value_error.missing"
                        }
                    ]
                }
            }
        }
    },
    "500": {
        "description": "Внутренняя ошибка сервера",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Internal server error"
                }
            }
        }
    }
}


def custom_openapi(app):
    """
    Настройка кастомной OpenAPI схемы.
    
    Args:
        app: FastAPI приложение
        
    Returns:
        dict: Настроенная OpenAPI схема
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
        routes=app.routes,
        tags=TAGS_METADATA,
        servers=SERVERS
    )
    
    # Добавление схем безопасности
    openapi_schema["components"] = {
        "securitySchemes": SECURITY_SCHEMES
    }
    
    # Добавление глобальных ответов
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method in ["get", "post", "put", "delete", "patch"]:
                openapi_schema["paths"][path][method]["responses"].update(GLOBAL_RESPONSES)
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema 