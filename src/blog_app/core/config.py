from pathlib import Path
from zoneinfo import ZoneInfo

from dynaconf import Dynaconf
from pydantic import AnyUrl, BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = PROJECT_ROOT / "config.toml"
DOTENV_PATH = PROJECT_ROOT / ".env"

_settings = Dynaconf(
    load_dotenv=True,
    _dotenv_path=DOTENV_PATH,
    environments=True,
    env_switcher="BLOG_APP_APP_ENV",
    envvar_prefix="BLOG_APP",
    settings_files=[CONFIG_PATH],
)


def get_db_dsn(async_: bool = True) -> str:
    if async_:
        driver = "postgresql+asyncpg"
    else:
        driver = "postgresql+psycopg"
    db_dsn = AnyUrl.build(
        scheme=driver,
        username=_settings.database.user,
        password=_settings.database.password,
        host=_settings.database.host,
        port=_settings.database.port,
        path=_settings.database.name,
    )
    return str(db_dsn)


def get_redis_dsn() -> str:
    return f"redis://{_settings.redis.host}:{_settings.redis.port}/{_settings.redis.db}"


def get_celery_broker_url() -> str:
    return (
        "amqp://"
        f"{_settings.rabbitmq.user}:{_settings.rabbitmq.password}"
        f"@{_settings.rabbitmq.host}:{_settings.rabbitmq.port}//"
    )


class Settings(BaseModel):
    app_name: str
    app_version: str
    timezone: str
    zone_info: ZoneInfo
    app_env: str
    db_dsn_async: str
    db_dsn_sync: str
    redis_dsn: str
    celery_broker_url: str
    debug: bool
    jwt_algorithm: str
    jwt_access_ttl_minutes: int
    jwt_refresh_ttl_minutes: int
    jwt_access_secret: str
    jwt_refresh_secret: str
    user_cache_ttl_minutes: int
    rabbitmq_queue: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_from_email: str
    smtp_from_name: str
    smtp_use_tls: bool
    s3_endpoint_url: str
    s3_public_url: str
    s3_region: str
    s3_bucket: str
    s3_access_key: str
    s3_secret_key: str
    s3_article_images_prefix: str
    s3_article_image_max_size_bytes: int


settings = Settings(
    app_name=_settings.app_name,
    app_version=_settings.version,
    timezone=_settings.timezone,
    zone_info=ZoneInfo(_settings.timezone),
    app_env=_settings.app_env,
    db_dsn_async=get_db_dsn(async_=True),
    db_dsn_sync=get_db_dsn(async_=False),
    redis_dsn=get_redis_dsn(),
    celery_broker_url=get_celery_broker_url(),
    debug=_settings.debug,
    jwt_algorithm=_settings.jwt.algorithm,
    jwt_access_ttl_minutes=int(_settings.jwt.access_token_expire_minutes),
    jwt_refresh_ttl_minutes=int(_settings.jwt.refresh_token_expire_minutes),
    jwt_access_secret=_settings.jwt.access_token_secret,
    jwt_refresh_secret=_settings.jwt.refresh_token_secret,
    user_cache_ttl_minutes=int(_settings.redis.user_cache_ttl_minutes),
    rabbitmq_queue=_settings.rabbitmq.queue,
    smtp_host=_settings.smtp.host,
    smtp_port=int(_settings.smtp.port),
    smtp_user=_settings.smtp.user,
    smtp_password=_settings.smtp.password,
    smtp_from_email=_settings.smtp.from_email,
    smtp_from_name=_settings.smtp.from_name,
    smtp_use_tls=_settings.smtp.use_tls,
    s3_endpoint_url=_settings.s3.endpoint_url,
    s3_public_url=_settings.s3.public_url,
    s3_region=_settings.s3.region,
    s3_bucket=_settings.s3.bucket,
    s3_access_key=_settings.s3.access_key,
    s3_secret_key=_settings.s3.secret_key,
    s3_article_images_prefix=_settings.s3.article_images_prefix,
    s3_article_image_max_size_bytes=int(_settings.s3.article_image_max_size_bytes),
)
