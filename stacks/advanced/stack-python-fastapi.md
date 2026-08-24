# Stack: Python + FastAPI

## Когда выбирать

API-сервисы, бэкенды с ML/данными, интеграционные сервисы, телеграм-боты. Фронт при необходимости — отдельно (Next.js) или Jinja для простых случаев. Не выбирать: продукты, где 90% ценности — богатый UI (там Next.js без отдельного бэка проще).

## Состав

- Python 3.12+, FastAPI, uvicorn
- SQLAlchemy 2.0 + Alembic (миграции) + PostgreSQL (Railway addon)
- Pydantic v2 (схемы запросов/ответов)
- Тесты: pytest + httpx (AsyncClient)
- Менеджер: uv (или poetry — зафиксировать при выборе)

## Структура проекта

```
src/
  main.py               ← создание app, подключение роутеров модулей
  modules/<domain>/     ← модульный монолит: router.py, service.py, models.py, schemas.py
  shared/               ← конфиг (pydantic-settings), db, общие утилиты
alembic/                ← миграции
tests/<domain>/
```

## Конвенции

- Модуль наружу отдаёт router и сервисные функции; чужие models напрямую не импортировать — только через сервисный слой владельца.
- Все входы/выходы API — Pydantic-схемы; ORM-модели наружу не отдавать.
- Конфиг — pydantic-settings из env; никакого чтения os.environ по коду.
- Функции, пока не нужны состояние/полиморфизм; async по умолчанию.

## Команды

`uv run uvicorn src.main:app --reload` · `uv run pytest` · `uv run ruff check` · `uv run alembic upgrade head` / `alembic revision --autogenerate`

## Деплой на Railway

- Start: `uvicorn src.main:app --host 0.0.0.0 --port $PORT` (порт — из env!).
- Миграции — в release/pre-deploy команду (`alembic upgrade head`), не в старт приложения.
- Healthcheck: GET /health → 200 + проверка коннекта к БД.
- Переменные: DATABASE_URL (Railway Postgres даёт сам), остальное — по .env.example.

## i18n

Для API — язык ответов/ошибок через заголовок Accept-Language + словари в src/shared/i18n/; для ботов — словари реплик по locale пользователя. Закладывать с M1, если мультиязычность возможна.

## Грабли

_(пополняется из проектов: дата — проект — что случилось — как избегать)_
