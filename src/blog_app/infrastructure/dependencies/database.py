from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from blog_app.core.database import AsyncSessionLocal


async def db_session() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
