# This is calclations for list. Size is not fixed.

from polyphony import testbench, pipelined
from polyphony.typing import List, int8

def add(a: List, b: List, c: List):
    for i in pipelined(range(len(a))):
        c[i] = a[i] + b[i]


def matmul(a: List, b: List, c: List, row: int8, col: int8):
    for i in range(row):
        for j in range(col):
            for k in range(col):
                c[i * col + j] += a[i * col + k] * b[k * col + j]


def append(a: List, c: List, item):
    for i in pipelined(range(len(a))):
        c[i] = a[i]
    c[len(a)] = item

