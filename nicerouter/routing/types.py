from fastapi import APIRouter
from fastapi.routing import APIRoute

# from nicerouter.routing import CreateRouterConfig
from nicerouter.routing.service.crud_service import CrudService
from nicerouter.routing.service.types import (
    EntiyType,
    InputType,
    OutputManyType,
    OutputType,
)


class NiceAPIRoute[
    Entity: EntiyType,
    Input: InputType,
    Output: OutputType,
    OutputMany: OutputManyType,
]:
    def __init__(
        self,
        route: APIRoute,
        service: CrudService[Entity, Input, Output, OutputMany],
    ) -> None:
        self.route = route
        self.service = service


class NiceAPIRouter[
    Entity: EntiyType,
    Input: InputType,
    Output: OutputType,
    OutputMany: OutputManyType,
]:
    def __init__(
        self,
        router: APIRouter,
        service: CrudService[Entity, Input, Output, OutputMany],
    ) -> None:

        self.api_router = router
        self._routes: list[NiceAPIRoute[Entity, Input, Output, OutputMany]] = []
        self.service = service

    def add_route(self, route: NiceAPIRoute[Entity, Input, Output, OutputMany]):
        self._routes.append(route)
        self.api_router.routes.append(route.route)
