from polyphony import pure, testbench
from polyphony.typing import int32, int64, uint32

PRECISION = 16


def add(a: int32, b: int32) -> int32:
    return a + b


def sub(a: int32, b: int32) -> int32:
    return a - b


def mult(a: int32, b: int32) -> int64:
    ab: int64 = a * b
    return ab >> PRECISION


def div(a: int32, b: int32) -> int64:
    a2: int64 = a << PRECISION
    return a2 // b
