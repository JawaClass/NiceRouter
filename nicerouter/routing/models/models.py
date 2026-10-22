from enum import Enum
from typing import Protocol, Sequence

from pydantic import BaseModel
from sqlalchemy.orm import Mapped


class ResponseType(Enum):
    Nested = "Nested"
    Normalized = "Normalized"


class HasIdMixin:
    id: Mapped[int]


# class HasIdBase(Protocol):  # , DeclarativeBase, HasIdMixin):
#     id: Mapped[int]


class BatchItemProtocol[E: BaseModel](Protocol):
    __module__ = "nicerouter.batch"
    id: int
    data: E


class BatchInputModelProtocol(Protocol):
    __module__ = "nicerouter.batch"
    items: Sequence[BatchItemProtocol]


def create_batch_input_model(
    input_model: type[BaseModel], name: str
) -> type[BaseModel]:
    class BatchItem(BaseModel):
        __qualname__ = f"{name}BatchItem"
        __module__ = "nicerouter.batch"
        id: int
        data: input_model  # type: ignore

    class BatchInputModel(BaseModel):
        __qualname__ = f"{name}BatchInputModel"
        __module__ = "nicerouter.batch"
        items: Sequence[BatchItem]

    return BatchInputModel


class DeleteEntityResponse(BaseModel):
    deleted_id: int


class DeleteBatchEntityResponse(BaseModel):
    deleted_count: int
