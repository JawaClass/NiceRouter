from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase
import sqlalchemy as sa

from nicerouter.sa_to_pydantic.sa_to_pydantic import sa_to_pydantic


def generate_model_schema_out(
    model: type[DeclarativeBase],
    exclude_fields: list[str] | None = None,
    base_model: type[BaseModel] | None = None,
):
    return sa_to_pydantic(
        model=model,
        exclude_fields=exclude_fields,
        name_generator=lambda name: f"{name}__Out",
        base_model=base_model,
        circular_depency_strategy="discard"
    )


def generate_model_schema_in(
    model: type[DeclarativeBase],
    exclude_fields: list[str] | None = None,
    base_model: type[BaseModel] | None = None,
):
    mapper = sa.inspect(model)
    relationships = mapper.relationships
    exclude_fields = exclude_fields or []
    exclude_fields = exclude_fields + list(relationships.keys())
    pk = [f.name for f in mapper.primary_key]
    exclude_fields = exclude_fields + pk
    return sa_to_pydantic(
        model=model,
        exclude_fields=exclude_fields,
        name_generator=lambda name: f"{name}__In",
        base_model=base_model,
        circular_depency_strategy="discard"
    )


def generate_model_schema_update(
    model: type[DeclarativeBase],
    exclude_fields: list[str] | None = None,
    base_model: type[BaseModel] | None = None,
):
    mapper = sa.inspect(model)
    relationships = mapper.relationships
    exclude_fields = exclude_fields or []
    exclude_fields = exclude_fields + list(relationships.keys())
    return sa_to_pydantic(
        model=model,
        exclude_fields=exclude_fields,
        name_generator=lambda name: f"{name}__Update",
        base_model=base_model,
        circular_depency_strategy="discard"
    )
