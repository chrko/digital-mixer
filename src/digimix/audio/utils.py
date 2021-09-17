import math
import shlex

_DIGITS_AMPLITUDE_CALC = 4


def precision_round(number, digits):
    power = f"{number:e}".split('e')[1]
    return round(number, -(int(power) - digits + 1))


def db_to_amplitude(level: float) -> float:
    return precision_round(math.sqrt(10 ** (level / 10)), _DIGITS_AMPLITUDE_CALC)


def amplitude_to_db(level: float) -> float:
    return precision_round(10 * math.log(level ** 2, 10), _DIGITS_AMPLITUDE_CALC)


def escape_pipeline_description(desc: str) -> str:
    return ' '.join(shlex.quote(arg) for arg in desc.replace('\n', ' ').split())
