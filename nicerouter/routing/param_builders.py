from fastapi import HTTPException
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.schema import Column


def is_column_field(db_class: object, field: str):
    attr = getattr(db_class, field)
    if not attr:
        return False

    return isinstance(attr, InstrumentedAttribute)


def build_filter_by(filter_by: str, db_class: object):
    filter_expresssions = filter_by.split(",")
    filters = []
    for filter_expr in filter_expresssions:
        field, value = filter_expr.split("=")
        if not is_column_field(db_class, field):
            raise HTTPException(
                status_code=400, detail=f"Invalid filter field: {field}"
            )

        col: Column = getattr(db_class.__table__.c, field)

        if not isinstance(col, Column):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid filter field: {field}. {type(col)} is not a column.",
            )

        try:
            py_type = col.type.python_type
            value_casted = py_type(value)  # cast the string to correct Python type
        except (ValueError, TypeError) as e:
            raise HTTPException(
                status_code=400, detail=f"Cannot cast value '{value}' to {py_type}: {e}"
            )

        filters.append(getattr(db_class, field) == value_casted)

    return filters


def build_sort_by(sort_by: str, db_class: object):
    order_columns = []
    fields = sort_by.split(",")
    for field in fields:
        desc = False
        if field.startswith("-"):
            desc = True
            field = field[1:]
        if not is_column_field(db_class, field):
            raise HTTPException(status_code=400, detail=f"Invalid sort field: {field}")
        col = getattr(db_class, field)
        order_columns.append(col.desc() if desc else col.asc())
    return order_columns


def get_db_class_fields(db_class: object):
    valid_attrs: dict[str, InstrumentedAttribute] = {
        attr: getattr(db_class, attr)
        for attr in dir(db_class)
        if isinstance(getattr(db_class, attr), InstrumentedAttribute)
    }
    return valid_attrs


def build_select_fields(db_class: object, exclude_fields_set: set[str]):
    db_class_fields = get_db_class_fields(db_class)
    load_only_fields = [
        field
        for name, field in db_class_fields.items()
        if name not in exclude_fields_set and not field.property._is_relationship
    ]
    return load_only_fields


def build_exclude_fields_set(exclude_fields: str):
    exclude_fields_list = (exclude_fields).replace(" ", "").split(",")
    exclude_fields_set = set(exclude_fields_list)
    return exclude_fields_set
