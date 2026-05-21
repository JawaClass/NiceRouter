from __future__ import annotations

from collections.abc import AsyncGenerator

import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from example.model import Base, ToDoItem, UrgencyLevel, User

# ----------------------
# Async DB setup (SQLite in-memory)
# ----------------------
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@event.listens_for(engine.sync_engine, "connect")
def enable_sqlite_fk_constraints(dbapi_connection, connection_record):
    print("enable_sqlite_fk_constraints....")
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_db()


async def seed_db():
    async with AsyncSession(engine) as session:
        # Check if we already have users
        result = await session.execute(sa.select(User))
        if result.scalars().first():
            print("Database already seeded")
            return

        # create some urgency levels
        low = UrgencyLevel(level="Low")
        medium = UrgencyLevel(level="Medium")
        high = UrgencyLevel(level="High")

        # Create some users
        alice = User(email="alice@example.com")
        bob = User(email="bob@example.com")

        # Create some todos
        todo1 = ToDoItem(name="Buy groceries", creator=alice, done=False, level=medium)
        todo2 = ToDoItem(
            name="Finish FastAPI project", creator=alice, done=True, level=low
        )
        todo3 = ToDoItem(
            name="Call mom", creator=bob, done=False, last_edit_user_xxx=bob, level=high
        )

        session.add_all([alice, bob, todo1, todo2, todo3])
        await session.commit()
        print("Dummy data inserted!")


# ----------------------
# Dependency for FastAPI
# ----------------------
async def get_db() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


def get_db_sync() -> AsyncSession:
    return AsyncSessionLocal()
