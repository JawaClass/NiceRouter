from sqlalchemy.orm import DeclarativeBase
from typing import Any, Literal, overload
from sqlalchemy.orm.collections import InstrumentedList

OnRecursion = Literal["raise", "ignore"]
 
def _sa_to_dict(
    obj: object, *, depth=None, path: dict | None = None, on_recursion: OnRecursion = "ignore"
):
    """
    Safely convert a SQLAlchemy DeclarativeBase object (or list of them)
    into plain Python dictionaries — avoiding circular references and
    unloaded relationships.
    """
    type_ = type(obj)

    # print(f"sa_to_dict: {depth=} {type(obj)}")

    if isinstance(obj, (type(None), int, float, str, bool)):
        return obj

    if depth is None:
        depth = 0

    if path is None:
        path = dict()  # dict is an ordered set

    if type_ in path:
        if on_recursion == "raise":
            path = [k.__name__ for k in path.keys()] # type: ignore
            msg = f"Circular Recursion detected @ {depth=} :: {type_=} in {path=}"
            raise ValueError(msg)
        else:
            return None

    # ORM-mapped class instance
    if isinstance(obj, DeclarativeBase):
        result = {}

        path[type_] = None

        for key, col_prop in obj.__mapper__.column_attrs.items():
            result[key] = getattr(obj, key)

        for key, rel_prop in obj.__mapper__.relationships.items():
            # only serialize if the relationship is loaded
            if key in obj.__dict__:
                result[key] = _sa_to_dict(
                    getattr(obj, key),
                    depth=depth + 1,
                    path=path,
                    on_recursion=on_recursion,
                )

        path.pop(type_)

        return result

    # Handle list-like relationships
    if isinstance(obj, (list, InstrumentedList, )): #
        return [_sa_to_dict(item, depth=depth + 1, path=path) for item in obj]

    # # Return plain value (non-SQLAlchemy type)
    # visited[obj_id] = obj
    return obj
