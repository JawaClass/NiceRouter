from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship, mapped_column
from pprint import pprint 

from nicerouter.sa_to_pydantic.sa_to_pydantic import sa_to_pydantic


class Base(DeclarativeBase):
    pass


class UrgencyLevel(Base):
    __tablename__ = "urgency_level"
    id: Mapped[int] = mapped_column(primary_key=True)
    level: Mapped[str] = mapped_column(sa.Text)

class ToDoItem(Base):
    __tablename__ = "todo_item"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.Text)
    creator_id: Mapped[int] = mapped_column(sa.ForeignKey("user.id"))
    creator: Mapped[User] = relationship(back_populates="todo_items")
    done: Mapped[bool] = mapped_column(sa.Boolean)
    level_id: Mapped[int | None] = mapped_column(sa.ForeignKey("urgency_level.id"))
    level: Mapped[UrgencyLevel | None] = relationship()

class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]
    todo_items: Mapped[list[ToDoItem]] = relationship(back_populates="creator") 


if __name__ == "__main__":
    m = sa_to_pydantic(model=ToDoItem, name_generator=lambda x: f"{x}__Out")
    print("m")
    print(m)
    pprint(m.model_fields)
    from nicerouter.normalization.type_builder import normalize_type
    norm = normalize_type(model_class=m)

    print("norm")
    print(norm)
    pprint(norm.model_fields)