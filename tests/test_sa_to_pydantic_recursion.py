from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from nicerouter.sa_to_pydantic.sa_to_pydantic import sa_to_pydantic
from nicerouter.sa_to_pydantic.sa_to_pydantic import REGISTRY
from pprint import pprint

class Base(DeclarativeBase):
    pass


class A(Base):
    __tablename__ = "a_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    foo: Mapped[str]
    bar: Mapped[int]
    optional: Mapped[int | None]

    b_id: Mapped[int] = mapped_column(sa.ForeignKey("b_table.id"))
    b: Mapped[B] = relationship(foreign_keys=b_id)


class B(Base):
    __tablename__ = "b_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    a_id: Mapped[int] = mapped_column(sa.ForeignKey("a_table.id"))
    a: Mapped[A] = relationship(foreign_keys=a_id)

    c_id: Mapped[int] = mapped_column(sa.ForeignKey("c_table.id"))
    c: Mapped[C] = relationship(foreign_keys=c_id)


class C(Base):
    __tablename__ = "c_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    a_id: Mapped[int] = mapped_column(sa.ForeignKey("a_table.id"))
    a: Mapped[A] = relationship(foreign_keys=a_id)


# def test_recursion():
#     print("test_recursion...")
#     REGISTRY.clear()
#     A_Out = sa_to_pydantic(
#         model=A,
#         name_generator=lambda name: f"{name}__Out",
#         circular_depency_strategy="discard",
#     )

#     c_mode_fields = (
#         A_Out.model_fields["b"].annotation.model_fields["c"].annotation.model_fields
#     )
#     assert "a" not in c_mode_fields
#     # print(c_mode_fields)


# def test_recursion2():
#     REGISTRY.clear()
#     A_Out = sa_to_pydantic(
#         model=A,
#         name_generator=lambda name: f"{name}__Out",
#         circular_depency_strategy="forwardref",
#     )

#     c_mode_fields = (
#         A_Out.model_fields["b"].annotation.model_fields["c"].annotation.model_fields
#     )
 
#     pprint(c_mode_fields)
#     assert "a" in c_mode_fields


# test_sa_to_pydantic_recursion
