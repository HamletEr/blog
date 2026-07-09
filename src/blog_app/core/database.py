from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# async_engine = create_async_engine("")  # TODO
#
# AsyncSessionLocal = async_sessionmaker(  # TODO
#     bind=async_engine,
#     class_=AsyncSession,
#     expire_on_commit=False,
#     autocommit=False,
#     autoflush=False,
# )
