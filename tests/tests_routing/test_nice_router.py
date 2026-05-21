import pytest
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from nicerouter.routing.repository.crud_repository import CrudRepository
from nicerouter.routing.service.crud_service import CrudService
from nicerouter.routing.service.entity_mappers.default_mapper import (
    DefaultServiceEntityMapper,
)
from tests import db  # import fxitures...  # noqa: F401


class Base(DeclarativeBase):
    pass


class A(Base):
    __tablename__ = "a"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()


class A_Input(BaseModel):
    name: str


class A_Output(BaseModel):
    id: int
    name: str


def create_repo():
    repo = CrudRepository(model_cls=A)
    return repo


def create_entity_mapper():
    entity_mapper = DefaultServiceEntityMapper(
        entity_cls=A, input_cls=A_Input, output_cls=A_Output
    )
    return entity_mapper


def create_service():
    repo = create_repo()
    entity_mapper = create_entity_mapper()

    crud_service = CrudService(
        entity_mapper=entity_mapper,
        repository=repo,
    )
    return crud_service


# @pytest.mark.asyncio
# async def test_create_crud_service(session: AsyncSession):

#     print("test_create_crud_service....")

#     crud_service = create_service()

#     a_input = A_Input(name="test")

#     a_entity = await crud_service.create(session, a_input)

#     assert a_entity.id is not None
#     assert a_entity.name == a_input.name
