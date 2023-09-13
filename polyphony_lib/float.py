from polyphony import pure, testbench
from polyphony.typing import int32

PRECISION = 16

def add(a: int32, b: int32) -> int32:
    return a + b

def sub(a: int32, b: int32) -> int32:
    return a - b

def mul(a: int32, b: int32) -> int32:
    return a * b >> PRECISION

def div(a: int32, b: int32) -> int32:
    return (a << PRECISION) // b

# @pure
# def fixed(a):
    # return int(a * (1 << PRECISION))

# @pure
# def float(a):
    # return a / (1 << PRECISION)


