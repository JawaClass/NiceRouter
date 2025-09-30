from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship, mapped_column
from pprint import pprint 
from pydantic import BaseModel
from src.sa_to_pydantic.sa_to_pydantic import sa_to_pydantic

class Base(DeclarativeBase):
        pass

class B(Base):
    __tablename__ = "b"
    id: Mapped[int] = mapped_column(primary_key=True)
    a_id: Mapped[int] = mapped_column(sa.ForeignKey("a_table.id"))
    a_id2: Mapped[int | None] = mapped_column(sa.ForeignKey("a_table.id"))

class A(Base):
    __tablename__ = "a_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    foo: Mapped[str]
    bar: Mapped[int]
    optional: Mapped[int | None]

    b: Mapped[B | None] = relationship(foreign_keys=[B.a_id2])
    b2: Mapped[B] = relationship(foreign_keys=[B.a_id])

 
class ToDoItem(Base):
    __tablename__ = "todo_item"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.Text)
    creator_id: Mapped[int] = mapped_column(sa.ForeignKey("user.id"))
    creator: Mapped[User] = relationship()
    done: Mapped[bool] = mapped_column(sa.Boolean)

class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]
    todo_items: Mapped[list[ToDoItem]] = relationship(back_populates="creator") 


def test():
    

    model = sa_to_pydantic(model=A, name_generator=lambda x : x)
    
    print("pydantic_model", model)
    pprint(model.model_fields)

    assert model.model_fields["foo"].is_required()
    assert model.model_fields["bar"].is_required()
    assert model.model_fields["id"].is_required()
    assert not model.model_fields["optional"].is_required()
    assert not model.model_fields["b"].is_required()
    assert model.model_fields["b2"].is_required()

    model.model_validate(A(id=1, foo="foo", bar=5, b2=B(id=1, a_id=999)))


def test2():
    sa_to_pydantic(
        model=A,
        exclude_fields=[],
        name_generator=lambda name: f"{name}__Out",
        base_model=BaseModel,
    )

    sa_to_pydantic(
        model=A,
        exclude_fields=[],
        name_generator=lambda name: f"{name}__In",
        base_model=BaseModel,
    )

def test3():
    sa_to_pydantic(
        model=User,
        exclude_fields=[],
        name_generator=lambda name: f"{name}__Out",
        base_model=BaseModel,
    )

    sa_to_pydantic(
        model=User,
        exclude_fields=[],
        name_generator=lambda name: f"{name}__In",
        base_model=BaseModel,
    )

if __name__ == "__main__":
    test3()