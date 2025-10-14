from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship, mapped_column
from pprint import pprint 

from nicerouter.sa_to_pydantic.sa_to_pydantic import sa_to_pydantic


class Base(DeclarativeBase):
    pass

class ToDoItem(Base):
    __tablename__ = "todo_item"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.Text)
    creator_id: Mapped[int] = mapped_column(sa.ForeignKey("user.id"))
    creator: Mapped[User] = relationship(back_populates="todo_items")
    done: Mapped[bool] = mapped_column(sa.Boolean)

class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]
    todo_items: Mapped[list[ToDoItem]] = relationship(back_populates="creator") 

 