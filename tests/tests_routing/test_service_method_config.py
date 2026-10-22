from collections.abc import AsyncGenerator, Callable

import pytest
import sqlalchemy as sa
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from nicerouter.routing import build_router_config, create_router
from nicerouter.routing.exceptions import NiceRouterError
from nicerouter.routing.models.config_models import CreateRouterConfig
from nicerouter.routing.service import service_methods
from tests.tests_routing.conftest import Book

pytestmark = pytest.mark.anyio


@pytest.fixture
def make_client(engine, seeded):
    """Builds a client for /book whose router config can be customised."""
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async def get_db() -> AsyncGenerator[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    clients: list[AsyncClient] = []

    async def _make(configure: Callable[[CreateRouterConfig], None]) -> AsyncClient:
        config = build_router_config(db_class=Book)
        configure(config)

        app = FastAPI()

        @app.exception_handler(NiceRouterError)
        async def _handler(request: Request, exc: NiceRouterError):
            return JSONResponse(
                status_code=exc.status_code, content={"detail": exc.detail}
            )

        app.include_router(
            create_router(prefix="/book", get_db_session=get_db, config=config)
        )
        client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        clients.append(client)
        return client

    yield _make


@pytest.fixture
def book_count(engine):
    async def _count() -> int:
        async with async_sessionmaker(engine)() as session:
            return (
                await session.execute(sa.select(sa.func.count(Book.id)))
            ).scalar_one()

    return _count


async def test_custom_get_all_replaces_default(make_client):
    calls = []

    async def custom_get_all(**kwargs):
        calls.append(kwargs)
        return []

    def configure(config):
        config.get_all_route.service_method = custom_get_all

    client = await make_client(configure)
    r = await client.get("/book", params={"limit": 5, "sort_by": "-pages"})

    assert r.status_code == 200
    assert r.json() == []
    assert calls[0]["db_class"] is Book
    assert calls[0]["limit"] == 5
    assert calls[0]["sort_by"] == "-pages"


async def test_custom_get_by_id_receives_item_id(make_client):
    calls = []

    async def custom_get_by_id(**kwargs):
        calls.append(kwargs)
        return {"id": kwargs["item_id"], "title": "from custom"}

    def configure(config):
        config.get_by_id_route.service_method = custom_get_by_id

    client = await make_client(configure)
    r = await client.get("/book/1")

    assert r.status_code == 200
    assert r.json()["title"] == "from custom"
    assert calls[0]["item_id"] == 1


async def test_custom_delete_replaces_default(make_client, book_count):
    async def custom_delete(**kwargs):
        return {"deleted_id": 1234}

    def configure(config):
        config.delete_route.service_method = custom_delete

    client = await make_client(configure)
    before = await book_count()
    r = await client.delete("/book/1")

    assert r.json() == {"deleted_id": 1234}
    assert await book_count() == before  # the default delete did not run


async def test_postprocessor_runs_on_custom_result(make_client):
    async def custom_get_all(**kwargs):
        return [{"id": 1, "title": "x"}]

    async def postprocessor(response, db):
        return [{**item, "title": item["title"].upper()} for item in response]

    def configure(config):
        config.get_all_route.service_method = custom_get_all
        config.get_all_route.postprocessor = postprocessor

    client = await make_client(configure)
    r = await client.get("/book")

    assert r.json()[0]["title"] == "X"


async def test_custom_method_can_delegate_to_default(make_client):
    async def only_published(**kwargs):
        books = await service_methods.get_all(**kwargs)
        return [b for b in books if b["published"]]

    def configure(config):
        config.get_all_route.service_method = only_published

    client = await make_client(configure)
    r = await client.get("/book")

    assert {b["title"] for b in r.json()} == {"Alpha", "Gamma"}


async def test_patch_has_separate_single_and_batch_overrides(make_client):
    async def single(**kwargs):
        return {"id": kwargs["item_id"], "title": "single"}

    async def batch(**kwargs):
        return [{"id": 1, "title": "batch"}]

    def configure(config):
        config.patch_route.service_method = single
        config.patch_route.batch_service_method = batch

    client = await make_client(configure)

    r = await client.patch("/book/2", json={"title": "t", "pages": 1, "author_id": 1})
    assert r.json()["title"] == "single"

    r = await client.patch(
        "/book/batch",
        json={"items": [{"id": 1, "data": {"title": "t", "pages": 1, "author_id": 1}}]},
    )
    assert r.json()[0]["title"] == "batch"


async def test_default_still_used_without_service_method(make_client):
    client = await make_client(lambda config: None)
    r = await client.get("/book/1")

    assert r.json()["title"] == "Alpha"
