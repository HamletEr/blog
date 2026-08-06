# ruff: noqa: E402, I001
import asyncio
from dataclasses import dataclass
from pathlib import Path
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from blog_app.core.config import settings  # noqa: E402
from blog_app.core.database import AsyncSessionLocal, async_engine  # noqa: E402
from blog_app.infrastructure.models.articles import ArticleModel  # noqa: E402
from blog_app.infrastructure.models.categories import CategoryModel  # noqa: E402
from blog_app.infrastructure.models.users import UserModel  # noqa: E402
from blog_app.infrastructure.services.passwords import Argon2PasswordHasher  # noqa: E402

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "AdminPass123"
USER_EMAIL = "user@example.com"
USER_PASSWORD = "UserPass123"


@dataclass(frozen=True)
class UserSeed:
    username: str
    email: str
    password: str
    is_admin: bool = False


@dataclass(frozen=True)
class ArticleSeed:
    title: str
    content: str
    category_name: str
    is_active: bool = True


USERS = (
    UserSeed(
        username="admin",
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        is_admin=True,
    ),
    UserSeed(
        username="user",
        email=USER_EMAIL,
        password=USER_PASSWORD,
    ),
)

CATEGORY_NAMES = (
    "Python",
    "FastAPI",
    "PostgreSQL",
    "Архитектура",
    "DevOps",
)

ARTICLES = (
    ArticleSeed(
        title="Асинхронный Python в веб-приложении",
        content=(
            "Асинхронный Python помогает обрабатывать сетевые операции без "
            "блокировки воркера. В FastAPI это особенно полезно для работы "
            "с базой данных, очередями и внешними сервисами."
        ),
        category_name="Python",
    ),
    ArticleSeed(
        title="FastAPI и слои приложения",
        content=(
            "Архитектура приложения разделяет API, use cases, domain и "
            "infrastructure. Такой подход упрощает тестирование и замену "
            "конкретных реализаций репозиториев."
        ),
        category_name="FastAPI",
    ),
    ArticleSeed(
        title="Полнотекстовый поиск в PostgreSQL",
        content=(
            "GIN индекс и tsvector позволяют строить полноценный поиск по "
            "русскому тексту. Ранжирование помогает показать более релевантные "
            "статьи выше в списке."
        ),
        category_name="PostgreSQL",
    ),
    ArticleSeed(
        title="Миграции базы данных в production",
        content=(
            "Миграция должна учитывать существующие данные, блокировки и "
            "возможность отката. Alembic помогает версионировать изменения "
            "схемы базы данных."
        ),
        category_name="PostgreSQL",
    ),
    ArticleSeed(
        title="RabbitMQ и Celery для фоновых задач",
        content=(
            "Очередь сообщений отделяет HTTP-запрос от долгой фоновой работы. "
            "Celery получает задачу из RabbitMQ и выполняет отправку письма "
            "отдельным воркером."
        ),
        category_name="Архитектура",
    ),
    ArticleSeed(
        title="S3 object storage для изображений",
        content=(
            "Object key хранится в базе данных, а публичный URL строится на "
            "уровне приложения. Такой подход упрощает переход между MinIO, "
            "Yandex Object Storage и другими S3-совместимыми сервисами."
        ),
        category_name="DevOps",
    ),
    ArticleSeed(
        title="Soft delete и активные статьи",
        content=(
            "Флаг is_active позволяет скрывать удаленные статьи без физического "
            "удаления. Partial index ускоряет поиск только по активным данным."
        ),
        category_name="PostgreSQL",
    ),
    ArticleSeed(
        title="Черновик удаленной статьи",
        content=(
            "Эта неактивная статья нужна для проверки, что поиск и списки "
            "не возвращают данные с флагом is_active false."
        ),
        category_name="Архитектура",
        is_active=False,
    ),
)


async def get_or_create_category(
    session: AsyncSession, category_name: str
) -> CategoryModel:
    category = await session.scalar(
        select(CategoryModel).where(CategoryModel.name == category_name)
    )
    if category is not None:
        return category

    category = CategoryModel(name=category_name)
    session.add(category)
    await session.flush()
    return category


async def get_or_create_user(
    session: AsyncSession,
    password_hasher: Argon2PasswordHasher,
    user_seed: UserSeed,
) -> UserModel:
    user = await session.scalar(
        select(UserModel).where(UserModel.email == user_seed.email)
    )
    if user is not None:
        return user

    user = UserModel(
        username=user_seed.username,
        email=user_seed.email,
        hashed_password=await password_hasher.hash(user_seed.password),
        is_active=True,
        is_admin=user_seed.is_admin,
    )
    session.add(user)
    await session.flush()
    return user


async def get_or_create_article(
    session: AsyncSession,
    article_seed: ArticleSeed,
    categories_by_name: dict[str, CategoryModel],
) -> ArticleModel:
    article = await session.scalar(
        select(ArticleModel).where(ArticleModel.title == article_seed.title)
    )
    if article is not None:
        return article

    category = categories_by_name[article_seed.category_name]
    article = ArticleModel(
        is_active=article_seed.is_active,
        title=article_seed.title,
        content=article_seed.content,
        category_id=category.id,
        image_object_key=None,
    )
    session.add(article)
    await session.flush()
    return article


def ensure_development_environment() -> None:
    if settings.app_env != "development":
        raise RuntimeError("Dev seed can only be run with BLOG_APP_APP_ENV=development")


async def seed() -> None:
    ensure_development_environment()
    password_hasher = Argon2PasswordHasher()

    async with AsyncSessionLocal() as session:
        categories = [
            await get_or_create_category(session, category_name)
            for category_name in CATEGORY_NAMES
        ]
        categories_by_name = {category.name: category for category in categories}

        for user_seed in USERS:
            await get_or_create_user(session, password_hasher, user_seed)

        for article_seed in ARTICLES:
            await get_or_create_article(session, article_seed, categories_by_name)

        await session.commit()


async def main() -> None:
    try:
        await seed()
    finally:
        await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
