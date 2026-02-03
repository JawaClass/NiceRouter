from sqlalchemy.orm import DeclarativeBase
from nicerouter.routing.service.crud_service import BaseCrudService
from nicerouter.routing.repository.crud_base_repository import BaseCrudRepository
from sqlalchemy.ext.asyncio import AsyncSession

from nicerouter.routing.service.dto_mapper import EntityDtoMapper



class ServiceFactory[T: DeclarativeBase, ID]:
    """
    The Assembler. It knows how to build the Service and Repo.
    Users can override this to inject extra dependencies (like S3 clients or Mailers).
    """
    def __init__(
        self, 
        model_cls: type[T], 
        service_cls: type[BaseCrudService[T, ID]],
        repo_cls: type[BaseCrudRepository[T, ID]],
    ):
        self.model_cls = model_cls
        self.service_cls = service_cls
        self.repo_cls = repo_cls

    def create(self, db: AsyncSession) -> BaseCrudService[T, ID]:
        # The 'Assembly' happens here, once per request
        repo = self.repo_cls(session=db, model_cls=self.model_cls)
        return self.service_cls(repository=repo)
    
    