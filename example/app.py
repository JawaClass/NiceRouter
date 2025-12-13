from fastapi import FastAPI

from example.db import get_db, init_db
from example.model import ToDoItem, UrgencyLevel, User
from nicerouter.routing import create_router_for_db


async def lifespan(app: FastAPI):
    await init_db()

    yield


app = FastAPI(lifespan=lifespan)  # type: ignore

user_router = create_router_for_db(db_class=User, prefix="/user", get_db_session=get_db)


app.include_router(user_router)


todo_router = create_router_for_db(
    db_class=ToDoItem, prefix="/todos", get_db_session=get_db
)
app.include_router(todo_router)

urgency_router = create_router_for_db(
    db_class=UrgencyLevel, prefix="/urgency", get_db_session=get_db
)
app.include_router(urgency_router)
