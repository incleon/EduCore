SENSITIVE_FIELDS = {"hashed_password", "initial_password"}


def serialize_sqlalchemy_obj(obj, visited=None, depth=0, max_depth=4):
    if visited is None:
        visited = set()
    if obj is None:
        return None
    if isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    import datetime
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    if isinstance(obj, (list, tuple)):
        return [serialize_sqlalchemy_obj(item, visited.copy(), depth, max_depth) for item in obj]
    if hasattr(obj, '__table__'):
        if depth > max_depth:
            return None
        if id(obj) in visited:
            return None
        visited.add(id(obj))
        result = {}
        from sqlalchemy import inspect
        state = inspect(obj)
        for attribute in state.mapper.column_attrs:
            key = attribute.key
            if key not in SENSITIVE_FIELDS:
                result[key] = serialize_sqlalchemy_obj(
                    getattr(obj, key), visited.copy(), depth + 1, max_depth
                )
        # Include relationships only when SQLAlchemy has already loaded them.
        # This keeps responses useful without triggering an unbounded query graph.
        for relationship in state.mapper.relationships:
            key = relationship.key
            if key in obj.__dict__:
                result[key] = serialize_sqlalchemy_obj(
                    obj.__dict__[key], visited.copy(), depth + 1, max_depth
                )
        return result
    if hasattr(obj, 'value'):
        return obj.value
    return obj
