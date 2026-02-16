from collections.abc import Awaitable, Callable
from typing import Any

import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from nicerouter.normalization.normalizer import ObjectNormalizer
from nicerouter.routing.service.crud_service import CrudService


class GetByIdConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    response_model: type[BaseModel]
    normalizer: ObjectNormalizer | None = None
    query: sa.Select | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class GetAllConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    response_model: type[BaseModel]
    normalizer: ObjectNormalizer | None = None
    query: sa.Select | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

type PreProcessorCallable[INPUT_MODEL] = Callable[[INPUT_MODEL, AsyncSession], Awaitable[INPUT_MODEL]]

class CreateRouteConfig[INPUT_MODEL: BaseModel](BaseModel):
    input_model: type[INPUT_MODEL]
    response_model: type[BaseModel]
    normalizer: ObjectNormalizer | None = None
    preprocessor_input: Callable[[INPUT_MODEL, AsyncSession], Awaitable[INPUT_MODEL]] | None = None
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class PatchRouteConfig[INPUT_MODEL: BaseModel](BaseModel):
    input_model: type[BaseModel]
    response_model: type[BaseModel]
    preprocessor_input: PreProcessorCallable[INPUT_MODEL] | None = None



class DeleteRouteConfig(BaseModel):
    pass


class DeleteMultiRouteConfig(BaseModel):
    pass


class CreateRouterConfig(BaseModel):
    db_class: type[Any] 
    get_by_id_route: GetByIdConfig | None = None
    get_all_route: GetAllConfig | None = None
    create_route: CreateRouteConfig | None = None
    patch_route: PatchRouteConfig | None = None
    delete_route: DeleteRouteConfig | None = None
    delete_multi_route: DeleteMultiRouteConfig | None = None
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
