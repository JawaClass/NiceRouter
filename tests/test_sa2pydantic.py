from pydantic import BaseModel
from pydantic_core import PydanticUndefined


def test_keep_default_value():
    """
    Test that default values from Sqlalchemy models are correctly transferred to the generated Pydantic models, and that fields with defaults are not marked as required.
    """

    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

    from nicerouter.sa_to_pydantic.sa_to_pydantic import _sa_to_pydantic

    class Base(DeclarativeBase):
        pass

    class SaModel(Base):
        __tablename__ = "sa_model"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(default="default_name")
        tel: Mapped[str | None] = mapped_column(default=None)
        is_filtered: Mapped[bool] = mapped_column(default=False, server_default="false")

    PydanticA = _sa_to_pydantic(
        model=SaModel,
        name_generator=lambda x: x,
        namespace="",
        circular_depency_strategy="discard",
    )

    assert PydanticA and issubclass(PydanticA, BaseModel)  # type: ignore

    id_field = PydanticA.model_fields["id"]

    assert id_field.is_required()
    assert id_field.default is PydanticUndefined, (
        f"Expected id field to have default None, got {id_field.default}"
    )

    name_field = PydanticA.model_fields["name"]

    assert not name_field.is_required()
    assert name_field.default == "default_name"

    tel_field = PydanticA.model_fields["tel"]

    assert not tel_field.is_required()
    assert tel_field.default is None

    is_filtered_field = PydanticA.model_fields["is_filtered"]

    assert not is_filtered_field.is_required()
    assert is_filtered_field.default is False
