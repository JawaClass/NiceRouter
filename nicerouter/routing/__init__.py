from typing import AsyncGenerator, Callable
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from nicerouter.pydantic_util.asoptional import make_pydantic_model_optional
from nicerouter.routing.config_models import (
    CreateRouteConfig,
    CreateRouterConfig,
    CrudService,
    DeleteRouteConfig,
    GetAllConfig,
    GetByIdConfig,
    PatchRouteConfig,
)
from nicerouter.routing.model_generator import (
    generate_model_schema_in,
    generate_model_schema_out,
)

from nicerouter.routing.router_factories import (
    create_delete_by_id_route,
    create_delete_multi_route,
    create_get_by_id_route,
    create_get_multi_route,
    # create_patch_multi_route,
    create_patch_route,
    create_post_route,
    create_post_multi_route
)
from nicerouter.routing.types import  NiceAPIRouter

from nicerouter.routing.service.crud_service import CrudRepository
from nicerouter.routing.service.dto_mapper import EntityDtoMapperSameObjectImpl


def build_router_config(
    service: CrudService,
    # db_class: type[DeclarativeBase],
    # normalizer: ObjectNormalizer | None = None,
    model_scheme_in: type[BaseModel] | None = None,
    out_schema_optional_fields: bool = True,
):
    db_class = service.repository.model_cls
    if not issubclass(db_class, DeclarativeBase):
        raise ValueError(
            f"{db_class=} needs to inherit from sqlalchemy DeclarativeBase."
        )

    GoModelSchemaIn = model_scheme_in or generate_model_schema_in(db_class)
    GoModelSchemaOut = generate_model_schema_out(db_class)
    # GoModelSchemaUpdate = generate_model_schema_update(db_class)
    GoModelSchemaUpdate = GoModelSchemaIn

    if out_schema_optional_fields:
        GoModelSchemaOut = make_pydantic_model_optional(GoModelSchemaOut)

    return CreateRouterConfig(
        service=service,
        db_class=db_class,
        get_by_id_route=GetByIdConfig(
            response_model=GoModelSchemaOut,
            # normalizer=normalizer
        ),
        delete_route=DeleteRouteConfig(),
        create_route=CreateRouteConfig(
            input_model=GoModelSchemaIn,
            response_model=GoModelSchemaOut,
            # normalizer=normalizer,
        ),
        patch_route=PatchRouteConfig(
            input_model=GoModelSchemaUpdate, response_model=GoModelSchemaOut
        ),
        get_all_route=GetAllConfig(
            response_model=GoModelSchemaOut,
            # normalizer=normalizer
        ),
    )


def create_router_for_db(
    *,
    prefix: str,
    get_db_session: Callable[[], AsyncGenerator[AsyncSession, None]],
    db_class: type[DeclarativeBase],
    # normalizer: ObjectNormalizer | None = None,
) -> NiceAPIRouter:

    ModelSchemaIn = generate_model_schema_in(db_class)

    service = CrudService(
        repository=CrudRepository(model_cls=db_class),
        dto_mapper=EntityDtoMapperSameObjectImpl(
            entity_cls=db_class, dto_cls=ModelSchemaIn
        ),
    )
    router_config = build_router_config(service=service)

    return create_router(
        prefix=prefix, get_db_session=get_db_session, config=router_config
    )


def create_router(
    *,
    prefix: str,
    get_db_session: Callable[[], AsyncGenerator[AsyncSession, None]],
    config: CreateRouterConfig,
) -> NiceAPIRouter:
    nice_router = NiceAPIRouter(nice_config=config, router=APIRouter(prefix=prefix))
    nice_router.nice_config = config

    # db_class = config.db_class

    if config.create_route:
        nice_router.add_route(
            route=create_post_route(
                # db_class=db_class,
                input_model=config.create_route.input_model,
                response_model=config.create_route.response_model,
                get_db_session=get_db_session,
                prefix=prefix,
                # normalizer=config.create_route.normalizer,
                preprocessor_input=config.create_route.preprocessor_input,
                service=config.service,
            )
        )
        
        nice_router.add_route(
            route=create_post_multi_route( 
                input_model=config.create_route.input_model,
                response_model=config.create_route.response_model,
                get_db_session=get_db_session,
                prefix=prefix,
                # normalizer=config.create_route.normalizer,
                preprocessor_input=config.create_route.preprocessor_input,
                service=config.service,
            )
        )
        

    if config.patch_route:
        #     router.routes.append(
        #         create_batch_patch_route_varied(
        #             db_class=db_class,
        #             input_model=config.patch_route.input_model,
        #             response_model=config.patch_route.response_model,
        #             get_db_session=get_db_session,
        #             prefix=prefix,
        #         )
        #     )
        nice_router.add_route(
            create_patch_route(
                # db_class=db_class,
                input_model=config.patch_route.input_model,
                response_model=config.patch_route.response_model,
                get_db_session=get_db_session,
                prefix=prefix,
                preprocessor_input=config.patch_route.preprocessor_input,
                service=config.service,
            ),
        )

    if config.get_all_route:
        nice_router.add_route(
            create_get_multi_route(
                # db_class=db_class,
                get_db_session=get_db_session,
                response_model=config.get_all_route.response_model,
                prefix=prefix,
                # normalizer=config.get_all_route.normalizer,
                service=config.service,
            ),
        )

    if config.delete_route:
        nice_router.add_route(
            create_delete_by_id_route(
                get_db_session=get_db_session,
                prefix=prefix,
                service=config.service,
            ),
        )

    if config.delete_multi_route:
        nice_router.add_route(
            create_delete_multi_route(
                # db_class=db_class,
                get_db_session=get_db_session,
                prefix=prefix,
                service=config.service,
            ),
        )

    if config.get_by_id_route:
        nice_router.add_route(
            create_get_by_id_route(
                # db_class=db_class,
                response_model=config.get_by_id_route.response_model,
                get_db_session=get_db_session,
                # query=config.get_by_id_route.query,
                # normalizer=config.get_by_id_route.normalizer,
                prefix=prefix,
                service=config.service,
            ),
        )

    return nice_router
