from collections.abc import AsyncGenerator, Callable 
from fastapi import Depends, Response
from fastapi.routing import APIRoute
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from nicerouter.routing.types import NiceAPIRoute
from nicerouter.routing.routes_service import tags_from_prefix
from nicerouter.routing.service.crud_service import CrudService
from sqlalchemy.orm import DeclarativeBase

def create_delete_multi_route[T_DB: DeclarativeBase, DTO: BaseModel](
    *,
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    service: CrudService[T_DB, DTO],
    prefix: str,
) -> NiceAPIRoute:
     
    async def endpoint(
        id_list: list[int], db: AsyncSession = Depends(get_db_session) 
    ):  
                
        await service.delete_multi(session=db, id_list=id_list)
        
        return Response()

    route = NiceAPIRoute(
        route=APIRoute(path=f"{prefix}",
        methods=["DELETE"],
        tags=tags_from_prefix(prefix),  # type:ignore
        response_model=None,
        endpoint=endpoint),
        service=service,
    )
    
    return route
