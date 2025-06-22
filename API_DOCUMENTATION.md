# Messenger API Documentation

## Обзор

Messenger API - это современное REST API для мессенджера с поддержкой WebSocket для реального времени. API построен на FastAPI и предоставляет полный набор функций для создания мессенджера.

## Быстрый старт

### Установка и запуск

```bash
# Клонирование репозитория
git clone <repository-url>
cd messenger

# Установка зависимостей
poetry install

# Настройка переменных окружения
cp src/example_env .env
# Отредактируйте .env файл

# Запуск приложения
poetry run uvicorn src.main:app --reload
```

### Доступ к документации

После запуска приложения документация доступна по адресам:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Аутентификация

API использует JWT токены для аутентификации. Процесс аутентификации:

1. **Регистрация**: `POST /api/v1/auth/sign-up`
2. **Вход**: `POST /api/v1/auth/login`
3. **Использование токена**: Добавьте заголовок `Authorization: Bearer <access_token>`

### Пример аутентификации

```bash
# Регистрация
curl -X POST "http://localhost:8000/api/v1/auth/sign-up" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepassword123"
  }'

# Вход
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepassword123"
  }'
```

## Основные эндпоинты

### 🔐 Аутентификация

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/api/v1/auth/sign-up` | Регистрация нового пользователя |
| POST | `/api/v1/auth/login` | Вход пользователя |
| POST | `/api/v1/auth/refresh` | Обновление access токена |

### 💬 Управление чатами

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/api/v1/chats` | Создание нового чата |
| GET | `/api/v1/chats/history/{chat_id}` | История сообщений чата |

### 👥 Управление пользователями

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/api/v1/users/me` | Профиль текущего пользователя |
| PUT | `/api/v1/users/me` | Обновление профиля |
| GET | `/api/v1/users/search` | Поиск пользователей |
| GET | `/api/v1/users/{user_id}` | Информация о пользователе |

### 📱 Реальное время

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| WebSocket | `/api/v1/messages/ws/{chat_id}` | WebSocket для сообщений |

### 📊 Мониторинг

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/api/v1/monitoring/health` | Проверка состояния системы |
| GET | `/api/v1/monitoring/metrics` | Метрики производительности |
| GET | `/api/v1/monitoring/alerts` | Активные алерты |
| GET | `/api/v1/monitoring/connections` | Статистика WebSocket |
| GET | `/api/v1/monitoring/cache/status` | Статус кэша |
| POST | `/api/v1/monitoring/cache/clear` | Очистка кэша |
| GET | `/api/v1/monitoring/performance/summary` | Сводка производительности |

## Детальное описание эндпоинтов

### Аутентификация

#### POST /api/v1/auth/sign-up

Регистрация нового пользователя.

**Тело запроса:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Ответ (201):**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com"
}
```

#### POST /api/v1/auth/login

Вход пользователя.

**Тело запроса:**
```json
{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Ответ (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Управление чатами

#### POST /api/v1/chats

Создание нового чата.

**Заголовки:**
```
Authorization: Bearer <access_token>
```

**Тело запроса:**
```json
{
  "name": "Team Chat",
  "participants": [1, 2, 3]
}
```

**Ответ (201):**
```json
{
  "id": 1,
  "name": "Team Chat",
  "creator_id": 1,
  "participants": [1, 2, 3]
}
```

#### GET /api/v1/chats/history/{chat_id}

Получение истории сообщений чата с пагинацией.

**Параметры запроса:**
- `page`: Номер страницы (по умолчанию 1)
- `size`: Размер страницы (по умолчанию 20)

**Ответ (200):**
```json
{
  "items": [
    {
      "id": 1,
      "chat_id": 1,
      "sender_id": 1,
      "text": "Hello everyone!",
      "was_read": true,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

### WebSocket для реального времени

#### WebSocket /api/v1/messages/ws/{chat_id}

WebSocket соединение для обмена сообщениями в реальном времени.

**Параметры подключения:**
- `chat_id`: ID чата
- `token`: JWT токен (query parameter)

**Пример подключения:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/messages/ws/1?token=YOUR_TOKEN');

ws.onopen = function() {
  console.log('Connected to chat');
};

ws.onmessage = function(event) {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};

// Отправка сообщения
ws.send(JSON.stringify({
  type: 'message',
  text: 'Hello everyone!'
}));
```

**Типы сообщений:**
- `message`: Новое сообщение
- `typing`: Пользователь печатает
- `read`: Сообщение прочитано
- `join`: Пользователь присоединился
- `leave`: Пользователь покинул чат

### Мониторинг

#### GET /api/v1/monitoring/health

Проверка состояния системы.

**Ответ (200):**
```json
{
  "status": "healthy",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time": 0.05
    },
    "redis": {
      "status": "healthy",
      "response_time": 0.01
    },
    "websocket": {
      "status": "healthy",
      "active_connections": 10
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### GET /api/v1/monitoring/metrics

Получение метрик производительности.

**Ответ (200):**
```json
{
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
    "redis_connected": true
  }
}
```

## Коды ошибок

| Код | Описание | Пример |
|-----|----------|--------|
| 400 | Неверный запрос | Неверные данные в запросе |
| 401 | Не авторизован | Отсутствует или неверный токен |
| 403 | Доступ запрещен | Нет прав для доступа к ресурсу |
| 404 | Не найдено | Ресурс не существует |
| 422 | Ошибка валидации | Неверный формат данных |
| 500 | Внутренняя ошибка сервера | Ошибка на стороне сервера |
| 503 | Сервис недоступен | Система нездорова |

## Пагинация

API поддерживает пагинацию для списков. Используйте параметры:

- `page`: Номер страницы (по умолчанию 1)
- `size`: Размер страницы (по умолчанию 20)

**Пример:**
```
GET /api/v1/chats/history/1?page=2&size=10
```

## Примеры использования

### Полный цикл работы с API

```bash
# 1. Регистрация пользователя
curl -X POST "http://localhost:8000/api/v1/auth/sign-up" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepassword123"
  }'

# 2. Вход и получение токена
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepassword123"
  }' | jq -r '.access_token')

# 3. Создание чата
curl -X POST "http://localhost:8000/api/v1/chats" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Chat",
    "participants": [1]
  }'

# 4. Получение истории сообщений
curl -X GET "http://localhost:8000/api/v1/chats/history/1" \
  -H "Authorization: Bearer $TOKEN"

# 5. Проверка состояния системы
curl -X GET "http://localhost:8000/api/v1/monitoring/health"
```

### JavaScript/TypeScript примеры

```javascript
// Аутентификация
async function login(email, password) {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
  return response.json();
}

// Создание чата
async function createChat(name, participants, token) {
  const response = await fetch('/api/v1/chats', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name, participants }),
  });
  return response.json();
}

// WebSocket соединение
function connectToChat(chatId, token) {
  const ws = new WebSocket(`ws://localhost:8000/api/v1/messages/ws/${chatId}?token=${token}`);
  
  ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    console.log('New message:', message);
  };
  
  return ws;
}
```

## Разработка

### Структура проекта

```
src/
├── api/
│   ├── v1/
│   │   ├── auth.py          # Аутентификация
│   │   ├── chat.py          # Управление чатами
│   │   ├── messages.py      # WebSocket сообщения
│   │   ├── monitoring.py    # Мониторинг
│   │   └── users.py         # Управление пользователями
│   ├── docs.py              # Документация API
│   └── router.py            # Основной роутер
├── db/                      # База данных
├── schemas/                 # Pydantic схемы
├── services/                # Бизнес-логика
└── utils/                   # Утилиты
```

### Тестирование

```bash
# Запуск тестов
poetry run pytest

# Запуск тестов с покрытием
poetry run pytest --cov=src

# Запуск конкретных тестов
poetry run pytest tests/auth/test_integration/
```

### Линтинг и форматирование

```bash
# Проверка кода
poetry run flake8 src/
poetry run mypy src/

# Форматирование
poetry run black src/
poetry run isort src/
```

## Развертывание

### Docker

```bash
# Сборка образа
docker build -t messenger-api .

# Запуск контейнера
docker run -p 8000:8000 messenger-api
```

### Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f
```

## Безопасность

### Рекомендации

1. **Токены**: Используйте короткое время жизни для access токенов
2. **HTTPS**: Всегда используйте HTTPS в продакшене
3. **Валидация**: Валидируйте все входные данные
4. **Логирование**: Ведите логи всех операций
5. **Мониторинг**: Настройте алерты для критических ошибок

### Ограничения

- Максимальный размер сообщения: 1000 символов
- Максимальное количество участников в чате: 100
- Лимит запросов: 1000 запросов в минуту на пользователя

## Поддержка

- **Документация**: https://docs.messenger.example.com
- **Issues**: https://github.com/example/messenger/issues
- **Discussions**: https://github.com/example/messenger/discussions

## Лицензия

MIT License - см. файл LICENSE для деталей. 