import math


def db_to_amplitude(level: float) -> float:
    return math.sqrt(10 ** (level / 10))


def amplitude_to_db(level: float) -> float:
    return 10 * math.log(level ** 2, 10)
