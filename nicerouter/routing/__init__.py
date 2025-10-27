
from typing import Any, AsyncGenerator, Callable
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter
from nicerouter.normalization.normalizer import ObjectNormalizer
from nicerouter.routing.config_models import CreateRouteConfig, CreateRouterConfig, DeleteRouteConfig, GetAllConfig, GetByIdConfig, PatchRouteConfig
from nicerouter.routing.model_generator import generate_model_schema_in, generate_model_schema_out
from nicerouter.routing.routes_factory import create_batch_patch_route_varied, create_delete_multi_route, create_delete_route, create_get_all_route, create_get_by_id_route, create_patch_route, create_post_route


def build_router_config(db_class: type[Any], normalizer: ObjectNormalizer | None = None):
    GoModelSchemaIn = generate_model_schema_in(db_class)
    GoModelSchemaOut = generate_model_schema_out(db_class)
    # GoModelSchemaUpdate = generate_model_schema_update(db_class)
    GoModelSchemaUpdate = GoModelSchemaIn

    return CreateRouterConfig(
        db_class=db_class,
        get_by_id_route=GetByIdConfig(response_model=GoModelSchemaOut, normalizer=normalizer),
        delete_route=DeleteRouteConfig(),
        create_route=CreateRouteConfig(
            input_model=GoModelSchemaIn, response_model=GoModelSchemaOut, normalizer=normalizer
        ),
        patch_route=PatchRouteConfig(input_model=GoModelSchemaUpdate),
        get_all_route=GetAllConfig(response_model=GoModelSchemaOut, normalizer=normalizer),
    )


def create_router_for_db(
    *,
    prefix: str,
    get_db_session: Callable[[], AsyncGenerator[AsyncSession, None]],
    db_class: type[Any],
    normalizer: ObjectNormalizer | None = None
) -> APIRouter:

    router_config = build_router_config(db_class=db_class, normalizer=normalizer)

    return create_router(
        prefix=prefix, get_db_session=get_db_session, config=router_config
    )

def create_router(
    *,
    prefix: str,
    get_db_session: Callable[[], AsyncGenerator[AsyncSession, None]],
    config: CreateRouterConfig,
) -> APIRouter:
    router = APIRouter(prefix=prefix)

    db_class = config.db_class

    if config.create_route:
        router.routes.append(
            create_post_route(
                db_class=db_class,
                input_model=config.create_route.input_model,
                response_model=config.create_route.response_model,
                get_db_session=get_db_session,
                prefix=prefix,
                normalizer=config.create_route.normalizer,
                preprocessor_input=config.create_route.preprocessor_input,
            ),
        )

    if config.patch_route:
        router.routes.append(
            create_batch_patch_route_varied(
                db_class=db_class,
                input_model=config.patch_route.input_model,
                response_model=config.patch_route.response_model,
                get_db_session=get_db_session,
                prefix=prefix,
            )
        )
        router.routes.append(
            create_patch_route(
                db_class=db_class,
                input_model=config.patch_route.input_model,
                response_model=config.patch_route.response_model,
                get_db_session=get_db_session,
                prefix=prefix,
                preprocessor_input=config.patch_route.preprocessor_input,
            ),
        )

    if config.get_all_route:
        router.routes.append(
            create_get_all_route(
                db_class=db_class,
                get_db_session=get_db_session,
                response_model=config.get_all_route.response_model,
                prefix=prefix,
            ),
        )

    if config.delete_route:
        router.routes.append(
            create_delete_route(
                db_class=db_class,
                get_db_session=get_db_session,
                prefix=prefix,
            ),
        )

    if config.delete_multi_route:
        router.routes.append(
            create_delete_multi_route(
                db_class=db_class,
                get_db_session=get_db_session,
                prefix=prefix,
            ),
        )

    if config.get_by_id_route:
        router.routes.append(
            create_get_by_id_route(
                db_class=db_class,
                response_model=config.get_by_id_route.response_model,
                get_db_session=get_db_session,
                query=config.get_by_id_route.query,
                normalizer=config.get_by_id_route.normalizer,
                prefix=prefix,
            ),
        )

    return router
