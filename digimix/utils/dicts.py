def dict_to_tuple(val: dict) -> tuple:
    keys = list(val.keys())
    keys.sort()
    return tuple((key, val[key]) for key in keys)
