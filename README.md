# Audio uploader
![alt text](https://img.shields.io/badge/python-3.13.2-orange)

## Technology stack

1. FastAPI
2. SQLAlchemy + Alembic
3. PostgreSQL
4. Docker, docker compose

## Run

### Showroom

#### Run local environment stack
```shell
docker-compose -f docker-compose.show.yml up --build -d 
```

swagager_url  = `http://localhost:8000/api/swagger`

*Chat for user can be found in src/db/init_data/init_data.py*

websocker_url = `http://localhost:8000/ws/{chat_id}?token='Bearer {your_access_token_from_login_api}'`

*Test credentials for authrozation, can be found in src/db/init_data/init_data.py*

auth_headers = `{"Authorization": "Bearer {your_access_token_from_login_api}"`




### Dev

#### Run local environment stack
```shell
docker-compose up -d --build
```

### Pipeline
1. Get code 
2. Login by code #If use swagger, authrozie in it 'Bearer {your token}'
3. Make request

swagger_uri = /api/swagger

#### Export local envs
```shell
cat .env.example > .env.local

export $(grep -v "^#" .env.local | xargs)
```

#### Install poetry
```shell
pip install poetry
```

#### Install the project dependencies
```shell
cd src && poetry install
```

#### Spawn a shell within the virtual environment
```shell
poetry shell
```

#### Run the server
```shell
uvicorn main:app --reload
```

## Migrations

#### Generate new migration
```shell
alembic revision --autogenerate -m "Migration Name"
```

#### Run migrations
```shell
alembic upgrade head
```

#### Downgrade last migration
```shell
alembic downgrade -1
```

## Development

#### Make lint, tests
```shell
cd src && make lint
cd src && make test
```

#### Branch naming
```
feature/{feature-name-in-kebab-case}  # branch with new functionality, code
fix/{fix-name-in-kebab-case}  # branch with fix changes
```

#### Commit messages
```
+ {message}  # adding new functionality, code
- {message}  # removing functionality, code
! {message}  # changing functionality, code
```
