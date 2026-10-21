def tags_from_prefix(prefix: str) -> list[str]:
    return [prefix.strip("/").split("/")[0]]
