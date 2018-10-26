import inspect
import json

serializer = json.dumps
deserializer = json.loads

def bind_and_call(func, data):
    """
    Bind the keys of `data` to the arguments of `func` and call `func` with
    those arguments.

    :param func: A callable.
    :type func: callable

    :param data: A mapping object.
    :type data: dict, mapping
    """
    data = { key.replace('-', '_'): value for key, value in data.items() }
    bound = inspect.signature(func).bind(**data)
    return func(*bound.args, **bound.kwargs)
