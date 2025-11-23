from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from sqlalchemy import text

from .config import settings
from .models import Base  # مهم: اضافه شد


engine: AsyncEngine = create_async_engine(
    settings.database_url,
    future=True,
)


async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


# --------------------------
#   init_db برای SQLite dev
# --------------------------
async def init_db():
    """
    برای محیط توسعه:
    وقتی دیتابیس sqlite+aiosqlite باشد،
    جدول‌ها را اتوماتیک می‌سازد.
    """
    if settings.database_url.startswith("sqlite"):
        async with engine.begin() as conn:
            # به SQLAlchemy می‌گوید همه جداول را بسازد
            await conn.run_sync(Base.metadata.create_all)