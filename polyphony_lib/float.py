from polyphony import pure, testbench
from polyphony.typing import int64, int64, int128

PRECISION = 48


def add(a: int64, b: int64) -> int64:
    return a + b


def sub(a: int64, b: int64) -> int64:
    return a - b


def mult(a: int64, b: int64) -> int64:
    ab: int128 = a * b
    return ab >> PRECISION


def div(a: int64, b: int64) -> int64:
    a2: int128 = a << PRECISION
    return a2 // b
