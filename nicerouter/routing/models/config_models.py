from typing import Any

import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict

from nicerouter.normalization.normalizer import ObjectNormalizer
from nicerouter.routing.routes.routes_factory import (
    PostProcessor,
    PreProcessor,
    ServiceMethod,
)


class GetByIdConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    response_model: type[BaseModel]
    normalizer: ObjectNormalizer | None = None
    query: sa.Select | None = None
    preprocessor: PreProcessor | None = None
    postprocessor: PostProcessor | None = None
    service_method: ServiceMethod | None = None


class GetAllConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    response_model: type[BaseModel]
    normalizer: ObjectNormalizer | None = None
    query: sa.Select | None = None
    preprocessor: PreProcessor | None = None
    postprocessor: PostProcessor | None = None
    service_method: ServiceMethod | None = None


class CreateRouteConfig[INPUT_MODEL: BaseModel](BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    input_model: type[INPUT_MODEL]
    response_model: type[BaseModel]
    normalizer: ObjectNormalizer | None = None
    preprocessor: PreProcessor | None = None
    postprocessor: PostProcessor | None = None
    service_method: ServiceMethod | None = None


class PatchRouteConfig[INPUT_MODEL: BaseModel](BaseModel):
    input_model: type[BaseModel]
    response_model: type[BaseModel] | None = None
    preprocessor: PreProcessor | None = None
    postprocessor: PostProcessor | None = None
    service_method: ServiceMethod | None = None
    batch_service_method: ServiceMethod | None = None


class DeleteRouteConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    preprocessor: PreProcessor | None = None
    postprocessor: PostProcessor | None = None
    service_method: ServiceMethod | None = None


class DeleteMultiRouteConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    preprocessor: PreProcessor | None = None
    postprocessor: PostProcessor | None = None
    service_method: ServiceMethod | None = None


class CreateRouterConfig(BaseModel):
    db_class: type[Any]
    get_by_id_route: GetByIdConfig | None = None
    get_all_route: GetAllConfig | None = None
    create_route: CreateRouteConfig | None = None
    patch_route: PatchRouteConfig | None = None
    delete_route: DeleteRouteConfig | None = None
    delete_multi_route: DeleteMultiRouteConfig | None = None
