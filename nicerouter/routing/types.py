
from fastapi import APIRouter
from fastapi.routing import APIRoute

from nicerouter.routing import CreateRouterConfig
from nicerouter.routing.service.crud_service import CrudService
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel


class NiceAPIRoute[A: DeclarativeBase, B: BaseModel]:
    def __init__(self, route: APIRoute, service: CrudService[A, B]) -> None:
        self.route = route
        self.service = service


class NiceAPIRouter[A: DeclarativeBase, B: BaseModel]:
    def __init__(self, nice_config: CreateRouterConfig[A, B], router: APIRouter, service: CrudService[A, B]) -> None:
        self.nice_config = nice_config
        self.api_router = router
        self._routes: list[NiceAPIRoute] = []
        self.service = service

    def add_route(self, route: NiceAPIRoute):
        self._routes.append(route)
        self.api_router.routes.append(route.route)
 