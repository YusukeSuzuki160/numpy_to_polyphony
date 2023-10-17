# This is calclations for 1d list. Size is fixed.
import float
from polyphony import pipelined, testbench, unroll
from polyphony.typing import List, int8, int32, int64, int128

LEN = 3
PRECISION = 48


def transpose(a: List, c: List) -> None:
    for i in range(LEN):
        c[i] = a[i]


def add(a: List, b: List, c: List) -> None:
    for i in unroll(range(LEN)):
        c[i] = a[i] + b[i]


def add_scalar(a: List, b: int32, c: List) -> None:
    for i in unroll(range(LEN)):
        c[i] = a[i] + b


def sub(a: List, b: List, c: List) -> None:
    for i in unroll(range(LEN)):
        c[i] = a[i] - b[i]


def sub_scalar(a: List, b: int64, c: List) -> None:
    for i in unroll(range(LEN)):
        c[i] = a[i] - b


def matmult(a: List, b: List, col: int8, c: List) -> None:
    for i in range(col):
        for k in unroll(range(LEN)):
            a_signed = a[k]
            b_signed = b[k * LEN + i]
            c[i] += a_signed * b_signed


def matmult_float(a: List, b: List, col: int8, c: List) -> None:
    for i in range(col):
        for k in unroll(range(LEN)):
            a_signed = a[k]
            b_signed = b[k * LEN + i]
            c[i] += float.mult(a_signed, b_signed)


def sqrt(a: List, c: List) -> None:
    # Newton's method
    for i in unroll(range(LEN)):
        x = a[i]
        for _ in range(10):
            x = x - (x * x - a[i]) // (2 * x)
        c[i] = x


def append(a: List, item: int64, c: List) -> None:
    for i in unroll(range(LEN)):
        c[i] = a[i]
    c[len(a)] = item


def argsort(a: List, c: List) -> None:
    for i in unroll(range(LEN)):
        c[i] = i
    for i in range(LEN):
        for j in range(i + 1, LEN):
            if a[c[i]] > a[c[j]]:
                tmp = c[i]
                c[i] = c[j]
                c[j] = tmp


def slice_by_array(a: List, b: List, c: List) -> None:
    for i in unroll(range(LEN)):
        c[i] = a[b[i]]


def mean(a: List) -> int64:
    s = 0
    for i in range(LEN):
        s += a[i]
    return s // LEN


def linalg_norm(A: List) -> int64:
    s: int64 = 0
    A_signed: int64 = 0
    for i in range(LEN):
        A_signed = A[i]
        A2 = float.mult(A_signed, A_signed)
        s += A2
    # Newton's method
    x: int128 = s
    if x == 0:
        return 0
    count: int8 = 100
    while count > 0:
        x2: int128 = x * x >> PRECISION
        x3: int128 = (x2 - s) << PRECISION
        x4: int128 = x << 1
        x5: int128 = x3 // x4
        if x5 < 10 and x5 > -10:
            count = 0
        else:
            count -= 1
            x -= x5
    if x < 0:
        return -x
    else:
        return x
