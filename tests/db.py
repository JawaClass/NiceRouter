import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from tests.tests_routing.test_nice_router import A  # import your models

DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine(DATABASE_URL, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(A.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def session(engine):
    async_session = sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async with async_session() as session:  # type: ignore
        async with session.begin():
            yield session
            await session.rollback()
