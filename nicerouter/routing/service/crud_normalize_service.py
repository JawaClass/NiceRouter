from abc import ABC, abstractmethod
from typing import Any, Iterable, Sequence 
from sqlalchemy.orm import DeclarativeBase 
from nicerouter.routing.repository.crud_base_repository import BaseCrudRepository
from nicerouter.routing.repository.crud_repository import CrudRepository
from nicerouter.routing.service.service_util import check_entity_found
from pydantic import BaseModel
from nicerouter.routing.service.model_types import BatchInputModel_ContainerType, BatchItem_ContainerType
from nicerouter.routing.service.crud_service import CrudService
 

class CrudNormalizeService[T: DeclarativeBase](CrudService):

    def __init__(self, repository: CrudRepository[T]) -> None:
        super().__init__(repository)
        
