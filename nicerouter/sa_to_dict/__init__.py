from sqlalchemy.orm import DeclarativeBase
from typing import Any, Iterable, Literal, overload
from sqlalchemy.orm.collections import InstrumentedList

from nicerouter.sa_to_dict.sa_to_dict import OnRecursion, _sa_to_dict
 

# 1. Define the overload for a single SQLAlchemy object -> returns a dict
@overload
def sa_to_dict(
    obj: DeclarativeBase, *, on_recursion: OnRecursion = "ignore"
) -> dict[str, Any]: ...

# 2. Define the overload for a list/collection -> returns a list
@overload
def sa_to_dict(
    obj: Iterable, *, on_recursion: OnRecursion = "ignore"
) -> list[dict[str, Any]]: ...

def sa_to_dict(
    obj: DeclarativeBase | Iterable, *, on_recursion: OnRecursion = "ignore"
):
    result = _sa_to_dict(obj=obj, on_recursion=on_recursion)

    if isinstance(result, dict):
        return result
    
    if isinstance(result, list):
        return result
    
    raise ValueError(f"Fatal error: sa_to_dict evaluated {type(result)}.")
