# This is calclations for list. Size is fixed.

from polyphony import testbench, pipelined, unroll
from polyphony.typing import List, int32

ROW = 2
COL = 2
LEN = ROW * COL

def add(a: List, b: List, c: List):
    for i in unroll(range(LEN)):
        c[i] = a[i] + b[i]


def matmult(a: List, b: List, col, c: List):
    for i in range(col):
        for j in range(ROW):
            for k in unroll(range(COL)):
                c[i * COL + j] += a[i * COL + k] * b[k * COL + j]


def append(a: List, item: int32, c: List):
    for i in unroll(range(LEN)):
        c[i] = a[i]
    c[len(a)] = item
