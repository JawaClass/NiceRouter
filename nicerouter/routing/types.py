
from fastapi import APIRouter
from fastapi.routing import APIRoute

from nicerouter.routing import CreateRouterConfig
from nicerouter.routing.service.crud_base_service import BaseCrudService



class NiceAPIRoute:
    def __init__(self, route: APIRoute, service: BaseCrudService) -> None:
        self.route = route
        self.service = service


class NiceAPIRouter:
    def __init__(self, nice_config: CreateRouterConfig, router: APIRouter) -> None:
        self.nice_config = nice_config
        self.api_router = router
        self._routes: list[NiceAPIRoute] = []

    def add_route(self, route: NiceAPIRoute):
        self._routes.append(route)
        self.api_router.routes.append(route.route)