from zoneinfo import ZoneInfo

from dynaconf import Dynaconf
from pydantic import AnyUrl
from pydantic_settings import BaseSettings

_settings = Dynaconf(
    load_dotenv=True,
    environments=True,
    env_switcher="BLOG_APP_ENV",
    envvar_prefix="BLOG_APP",
    settings_files=["config.toml"],
)

_db_dsn = AnyUrl.build(
    scheme="postgresql+asyncpg",
    username=_settings.database.user,
    password=_settings.database.password,
    host=_settings.database.host,
    port=_settings.database.port,
    path=_settings.database.name,
)


class Settings(BaseSettings):
    app_name: str
    timezone: str
    zone_info: ZoneInfo
    app_env: str
    db_dsn: str
    debug: bool


settings = Settings(
    app_name=_settings.app_name,
    timezone=_settings.timezone,
    zone_info=ZoneInfo(_settings.timezone),
    app_env=_settings.app_env,
    db_dsn=str(_db_dsn),
    debug=_settings.debug,
)
