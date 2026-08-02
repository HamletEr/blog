# Blog

API корпоративного блога.

Проект построен на FastAPI. Для хранения данных используется PostgreSQL, для
кеша и refresh-токенов - Redis, для фоновых задач - Celery с RabbitMQ. Для хранения 
изображений для статей используется S3(Minio). Почтовые уведомления _при локальной 
разработке_ отправляются в Mailpit. 


### Окружение

- Python 3.12.13
- uv
- Make
- Docker и Docker Compose

Python-зависимости описаны в `pyproject.toml`. Установка: 

```bash
uv sync
```

### Конфигурация

В проекте используются два источника конфигурации:

- `.env` - секреты и значения, необходимые для Docker Compose;
- `config.toml` - несекретные настройки и локальные значения по умолчанию.

Для первичной настройки:

```bash
cp .env.example .env
```

### Быстрый запуск

```text
uv sync                      # подготовить окружение
cp -n .env.example .env      # копировать .env (linux/mac) или `copy` в Win
make dev-db-migrate          # поднять БД и применить миграции
make dev-seed                # заполнить БД демо-данными
make up                      # поднять все сервисы
```

Будут подняты:

- FastAPI-приложение;
- PostgreSQL;
- Redis;
- RabbitMQ;
- Celery worker;
- Minio + образ для инициализации бакетов
- Mailpit.

Остановить контейнеры:

```bash
make down
```

### Полезные адреса

Swagger UI:

```text
http://localhost:8000/docs
```

RabbitMQ Management:

```text
http://localhost:15672
```

Mailpit:

```text
http://localhost:8025
```

Minio UI:

```text
http://localhost:9001
```

* _Порты задаются в `.env`, поэтому фактические адреса могут отличаться._

### Проверки

Lint, format и mypy:

```bash
make check
```

Тесты с coverage:

```bash
make tests
```

Интеграционные тесты, которым нужен Redis, пропускаются фикстурами, если Redis
недоступен.

### Архитектура

Проект построен по src-layout. Слои:

- `domain` - сущности, интерфейсы, доменные исключения и контракты сервисов;
- `use_cases` - прикладные сценарии;
- `infrastructure` - реализации репозиториев, сервисов и FastAPI-зависимостей;
- `core` - конфиги
- `api` - HTTP-маршруты, схемы, middleware и exception handlers;
- `tasks` - Celery app и фоновые задачи.

### Mailpit

Mailpit используется только для локальной разработки. Это SMTP-сервер, который
принимает письма и показывает их в web UI.

Внутри Docker Compose приложение и worker отправляют письма на:

```text
BLOG_APP_SMTP__HOST=blog_app_mailpit
BLOG_APP_SMTP__PORT=1025
```

С хост-машины письма можно смотреть здесь:

```text
http://localhost:8025
```

Адрес получателя может быть любым. Mailpit не проверяет, существует ли такой
email, и не отправляет письмо наружу.

Для реального SMTP-провайдера достаточно заменить SMTP-переменные в `.env`.

### RabbitMQ и Celery

В `docker-compose.yml` намеренно используется:

```yaml
image: rabbitmq:3.13-management
```

Причина: RabbitMQ 4.x строже относится к устаревшим transient non-exclusive
queues, которые Celery/Kombu использует при старте worker для служебного
механизма `mingle`/`control`. С `rabbitmq:4-management` worker может подключиться
к брокеру, но затем циклически падать с ошибкой: 
`Feature `transient_nonexcl_queues` is deprecated.`
В таком состоянии задачи видны в RabbitMQ, но worker их не обрабатывает.

RabbitMQ `3.13-management` выбран как стабильный вариант совместимый с 
Celery 5.x. Если позже потребуется RabbitMQ 4.x, нужно в обязательном порядке
проверять совместимость с Celery.

### Частые команды

```bash
uv sync
make help
make up
make down
make check
make tests
```
_**Полный список команд в `Makefile`.**_

Локальный запуск FastAPI:

```bash
uv run uvicorn --app-dir src blog_app.main:app --reload
```

Локальный запуск Celery worker:

```bash
uv run celery -A blog_app.tasks.celery_app:celery_app worker --loglevel=info
```
