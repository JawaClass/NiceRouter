from fastapi import FastAPI
from pydantic import BaseModel

from example.db import get_db, init_db
from example.model import Panda, ToDoItem, UrgencyLevel, User
from nicerouter.routing import create_router_for_db

"""
How to run: 
uv run -m fastapi run example/app.py
"""

async def lifespan(app: FastAPI):
    await init_db()

    yield


app = FastAPI(lifespan=lifespan)  # type: ignore

user_router = create_router_for_db(db_class=User, prefix="/user", get_db_session=get_db)

user_service = user_router.service


app.include_router(user_router.api_router)


todo_router = create_router_for_db(
    db_class=ToDoItem, prefix="/todos", get_db_session=get_db
)
app.include_router(todo_router.api_router)

urgency_router = create_router_for_db(
    db_class=UrgencyLevel, prefix="/urgency", get_db_session=get_db
)
app.include_router(urgency_router.api_router)


pandas_router = create_router_for_db(
    db_class=Panda, prefix="/pandas", get_db_session=get_db
)
 
app.include_router(pandas_router.api_router)
