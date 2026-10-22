from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.pool import StaticPool

from nicerouter.routing import create_router_for_db
from nicerouter.routing.exceptions import NiceRouterError


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "author"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.Text)
    email: Mapped[str] = mapped_column(sa.Text, unique=True)
    books: Mapped[list[Book]] = relationship(
        back_populates="author", passive_deletes="all"
    )


class Book(Base):
    __tablename__ = "book"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(sa.Text)
    pages: Mapped[int] = mapped_column(sa.Integer)
    published: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    author_id: Mapped[int] = mapped_column(sa.ForeignKey("author.id"))
    author: Mapped[Author] = relationship(back_populates="books")


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _fk_on(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db(engine) -> AsyncGenerator[AsyncSession]:
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session


@pytest.fixture
async def seeded(db: AsyncSession):
    alice = Author(name="Alice", email="alice@example.com")
    bob = Author(name="Bob", email="bob@example.com")
    db.add_all(
        [
            alice,
            bob,
            Book(title="Alpha", pages=100, published=True, author=alice),
            Book(title="Beta", pages=300, published=False, author=alice),
            Book(title="Gamma", pages=200, published=True, author=bob),
        ]
    )
    await db.commit()


@pytest.fixture
async def client(engine, seeded) -> AsyncGenerator[AsyncClient]:
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async def get_db() -> AsyncGenerator[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    app = FastAPI()

    # The library only raises NiceRouterError; mapping to HTTP is the app's job.
    @app.exception_handler(NiceRouterError)
    async def _handler(request: Request, exc: NiceRouterError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    app.include_router(
        create_router_for_db(db_class=Author, prefix="/author", get_db_session=get_db)
    )
    app.include_router(
        create_router_for_db(db_class=Book, prefix="/book", get_db_session=get_db)
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
