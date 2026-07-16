from pathlib import Path
from zoneinfo import ZoneInfo

from dynaconf import Dynaconf
from pydantic import AnyUrl
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = PROJECT_ROOT / "config.toml"
DOTENV_PATH = PROJECT_ROOT / ".env"

_settings = Dynaconf(
    load_dotenv=True,
    _dotenv_path=DOTENV_PATH,
    environments=True,
    env_switcher="BLOG_APP_ENV",
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


class Settings(BaseSettings):
    app_name: str
    app_version: str
    timezone: str
    zone_info: ZoneInfo
    app_env: str
    db_dsn_async: str
    db_dsn_sync: str
    debug: bool


settings = Settings(
    app_name=_settings.app_name,
    app_version=_settings.version,
    timezone=_settings.timezone,
    zone_info=ZoneInfo(_settings.timezone),
    app_env=_settings.app_env,
    db_dsn_async=get_db_dsn(),
    db_dsn_sync=get_db_dsn(async_=False),
    debug=_settings.debug,
)
