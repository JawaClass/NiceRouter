from fastapi import FastAPI
from nicerouter.normalization.normalizer import ObjectNormalizer
from nicerouter.routing import create_router_for_db
from example.model import User, ToDoItem, UrgencyLevel
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

app.include_router(
    create_router_for_db(
    db_class=UrgencyLevel,
    prefix="/urgency",
    get_db_session=get_db
    )
)

from nicerouter.sa_to_pydantic.sa_to_pydantic import REGISTRY

from pprint import pprint

print("sa_to_pydantic REGISTRY")
for namespace in REGISTRY:
    print("Namespace --- ", namespace)
    for model_name, entry in REGISTRY[namespace].items():
        if "__Out" in model_name:
            print("   ", model_name)
            print("      ", entry.model)
            pprint(entry.model.model_fields)
            print("")