# Builder Stage, create venv with dependecies
FROM python:3.13-alpine AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_OPTIONS_NO_PIP=true \
    POETRY_VIRTUALENVS_OPTIONS_NO_SETUPTOOLS=true \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/venv/bin:${PATH}" \
    VIRTUAL_ENV=/venv

ARG DEV_DEPS=False

COPY ./src/pyproject.toml ./src/poetry.lock ./

RUN apk add build-base zlib-dev\
  && pip install --no-cache-dir poetry \
  && python -m venv /venv \
  && if [ $DEV_DEPS = True ] ; then \
       poetry install --no-root --no-cache --no-interaction --no-ansi && poetry add poetry ; else \
       poetry install --no-root --no-cache --no-interaction --no-ansi ; fi \
  && apk del build-base zlib-dev

# Final Stage
FROM python:3.13-alpine AS final

ARG DEV_DEPS=False

ENV PATH="/venv/bin:${PATH}" \
    VIRTUAL_ENV=/venv

RUN if [ $DEV_DEPS = True ] ; then apk update && apk add make; fi

WORKDIR /usr/src/app

# Copy venv with installed dependencies from builder stage
COPY --from=builder /venv /venv
COPY ./src ./src

WORKDIR /usr/src/app/src

CMD ["/venv/bin/python", "-m", "alembic", "upgrade", "head"]
CMD ["/venv/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "uvloop", "--http", "httptools"]
