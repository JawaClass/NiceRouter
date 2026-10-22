import pytest
from pydantic import BaseModel

from nicerouter.routing.routes import routes_factory as rf

pytestmark = pytest.mark.anyio

SENTINEL = object()


class Item(BaseModel):
    id: int = 1


async def _get_db():
    yield None


def _stub(calls):
    async def service_method(**kwargs):
        calls.append(kwargs)
        return SENTINEL

    return service_method


async def _noop(x, db):
    return x


@pytest.mark.parametrize(
    ("factory", "extra", "call"),
    [
        (rf.create_delete_route, {}, {"id": 1}),
        (rf.create_delete_multi_route, {}, {"id_list": [1, 2]}),
        (rf.create_patch_route, {"input_model": Item}, {"id": 1, "payload": Item()}),
        (
            rf.create_get_by_id_route,
            {"response_model": Item, "query": None},
            {"id": 1},
        ),
    ],
)
async def test_custom_service_method_replaces_default(factory, extra, call):
    calls = []
    route = factory(
        db_class=Item,
        get_db_session=_get_db,
        prefix="/x",
        postprocessor=_noop,
        service_method=_stub(calls),
        **extra,
    )
    kwargs = dict(call)
    kwargs["db"] = "db-session"
    result = await route.endpoint(**kwargs)

    assert result is SENTINEL
    assert len(calls) == 1
    assert calls[0]["db"] == "db-session"
    assert calls[0]["db_class"] is Item
