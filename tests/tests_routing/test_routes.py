import pytest

pytestmark = pytest.mark.anyio


async def test_get_all(client):
    r = await client.get("/book")
    assert r.status_code == 200
    assert {b["title"] for b in r.json()} == {"Alpha", "Beta", "Gamma"}


async def test_get_all_filter_sort_pagination(client):
    r = await client.get(
        "/book", params={"filter_by": "published=true", "sort_by": "-pages"}
    )
    assert [b["title"] for b in r.json()] == ["Gamma", "Alpha"]

    r = await client.get("/book", params={"sort_by": "pages", "limit": 1, "offset": 1})
    assert [b["title"] for b in r.json()] == ["Gamma"]


async def test_get_all_invalid_filter_is_400(client):
    r = await client.get("/book", params={"filter_by": "nope=1"})
    assert r.status_code == 400
    assert "Invalid filter field" in r.json()["detail"]


async def test_get_all_invalid_sort_is_400(client):
    r = await client.get("/book", params={"sort_by": "nope"})
    assert r.status_code == 400


async def test_get_all_normalized(client):
    r = await client.get("/book", params={"response_type": "Normalized"})
    assert r.status_code == 200
    assert isinstance(r.json(), dict)


async def test_get_by_id(client):
    r = await client.get("/book/1")
    assert r.status_code == 200
    assert r.json()["title"] == "Alpha"


async def test_get_by_id_missing_is_404(client):
    r = await client.get("/book/99")
    assert r.status_code == 404
    assert r.json() == {"detail": "Book not found"}


async def test_post(client):
    r = await client.post("/author", json={"name": "Cy", "email": "cy@example.com"})
    assert r.status_code == 200
    assert r.json()["name"] == "Cy"
    assert (await client.get(f"/author/{r.json()['id']}")).status_code == 200


async def test_post_unique_violation_is_400(client):
    r = await client.post("/author", json={"name": "Dup", "email": "alice@example.com"})
    assert r.status_code == 400


async def test_post_validation_error_is_422(client):
    r = await client.post("/author", json={"name": "NoEmail"})
    assert r.status_code == 422


async def test_patch(client):
    r = await client.patch(
        "/book/1",
        json={"title": "Alpha 2", "pages": 100, "author_id": 1, "published": True},
    )
    assert r.status_code == 200
    assert (await client.get("/book/1")).json()["title"] == "Alpha 2"


async def test_patch_missing_is_404(client):
    r = await client.patch(
        "/book/99",
        json={"title": "x", "pages": 1, "author_id": 1},
    )
    assert r.status_code == 404


async def test_delete(client):
    r = await client.delete("/book/3")
    assert r.status_code == 200
    assert r.json() == {"deleted_id": 3}
    assert (await client.get("/book/3")).status_code == 404


async def test_delete_missing_is_404(client):
    assert (await client.delete("/book/99")).status_code == 404


async def test_delete_referenced_is_409(client):
    r = await client.delete("/author/1")
    assert r.status_code == 409


async def test_unhandled_library_errors_propagate_without_app_handler(engine, seeded):
    """The library must not translate errors itself; the app decides."""
    from collections.abc import AsyncGenerator

    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from nicerouter.routing import create_router_for_db
    from nicerouter.routing.exceptions import NotFoundError
    from tests.tests_routing.conftest import Book

    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async def get_db() -> AsyncGenerator[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    app = FastAPI()
    app.include_router(
        create_router_for_db(db_class=Book, prefix="/book", get_db_session=get_db)
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        with pytest.raises(NotFoundError):
            await c.get("/book/99")
