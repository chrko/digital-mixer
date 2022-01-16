import math
import shlex
from itertools import chain

_DIGITS_AMPLITUDE_CALC = 4


def precision_round(number, digits):
    power = f"{number:e}".split("e")[1]
    return round(number, -(int(power) - digits + 1))


def db_to_amplitude(level: float) -> float:
    return precision_round(math.sqrt(10 ** (level / 10)), _DIGITS_AMPLITUDE_CALC)


def amplitude_to_db(level: float) -> float:
    return precision_round(10 * math.log(level ** 2, 10), _DIGITS_AMPLITUDE_CALC)


def linspace(x, y, steps):
    interval = (y - x) / (steps - 1)
    return tuple(x + step * interval for step in range(steps))


def interp(x, p0, p1):
    return p0[1] + (x - p0[0]) * (p1[1] - p0[1]) / (p1[0] - p0[0])


def make_discrete_to_continuous(
    x: tuple[int, int] = (0, 127),
    y: tuple[int, ...] = (-100, -70, -50, -30, -20, -10, -5, 0),
    edge_points: tuple[tuple[int, int], ...] = ((0, -math.inf),),
    cached=True,
):
    points = tuple(zip(linspace(x[0], x[1], len(y)), y))
    concrete_points = dict(chain(points, edge_points))

    def dtc(x_new):
        if x_new in concrete_points:
            return concrete_points[x_new]

        for i in range(len(points) - 1):
            if points[i][0] <= x_new < points[i + 1][0]:
                return precision_round(interp(x_new, points[i], points[i + 1]), 4)

        raise ValueError(f"unable to calculate x_new: {x_new}")

    if cached:
        pre_calc = list(dtc(x_new) for x_new in range(x[0], x[1] + 1))

        def dtc_cached(x_new):
            try:
                return pre_calc[x_new - x[0]]
            except KeyError:
                raise ValueError(f"unable to calculate x_new: {x_new}")

        return dtc_cached

    return dtc


default_linear_fader_midi_to_db = make_discrete_to_continuous()


def escape_pipeline_description(desc: str) -> str:
    return " ".join(shlex.quote(arg) for arg in desc.replace("\n", " ").split())
