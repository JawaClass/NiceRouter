from fastapi import FastAPI
from nicerouter.routing import create_router_for_db
from example.model import User, ToDoItem
from example.db import get_db, init_db


async def lifespan(app: FastAPI):
    await init_db()
    
    yield

app = FastAPI(lifespan=lifespan) # type: ignore


app.include_router(
    create_router_for_db(
    db_class=User,
    prefix="/user",
    get_db_session=get_db
    )
)

app.include_router(
    create_router_for_db(
    db_class=ToDoItem,
    prefix="/todos",
    get_db_session=get_db
    )
)