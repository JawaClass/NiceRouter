
def check_entity_found[T](entity: T | None) -> T:
    if not entity:
        raise RuntimeError(f"Entity with id {id=} not found.")
    return entity
