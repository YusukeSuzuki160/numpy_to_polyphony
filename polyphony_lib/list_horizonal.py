# This is calclations for 1d list. Size is fixed.
import float
import div
from polyphony import pipelined, testbench, unroll
from polyphony.typing import List, int8, int16, int32, int64, int128

LEN: int16 = 5
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
    ans = s // LEN
    return ans


def linalg_norm(A: List) -> int64:
    s: int64 = 0
    A_signed: int64 = 0
    for i in range(LEN):
        A_signed = A[i]
        A2 = float.mult(A_signed, A_signed)
        s += A2
    # Newton's method
    # x: int64 = s
    # s_128 : int128 = s << PRECISION
    # ans = 0
    # if x != 0:
    #     count: int8 = 20
    #     while count > 0:
    #         x_2: int64 = s_128 // x
    #         x_3: int64 = (x - x_2) >> 1
    #         if x_3 < 10 and x_3 > -10:
    #             count = 0
    #         else:
    #             count -= 1
    #             x -= x_3
    # if x < 0:
    #     ans = -x
    # else:
    #     ans = x
    ans = sqrt_scalar(s)
    return ans

def sqrt_scalar(s: int64) -> int64:
    # Newton's method
    x: int64 = 281474976710656
    x_x: int128 = x * x
    x_x_2: int64 = x_x >> PRECISION
    cond: int128 = s * x_x_2 >> PRECISION
    while cond >= 844424930131968:
        x = x >> 1
        x_x = x * x
        x_x_2 = x_x >> PRECISION
        cond = s * x_x_2 >> PRECISION
    count = 25
    ans: int128 = 0
    while count > 0:
        x_2: int128 = x * x >> PRECISION
        x_3: int128 = s * x_2 >> PRECISION
        x_4: int64 = 844424930131968 - x_3
        x_5: int128 = x_4 >> 1
        x_6: int128 = x * x_5 >> PRECISION
        if x - x_6 < 100000000 and x - x_6 > -100000000:
            count = 0
        else:
            count -= 1
            x = x_6
    if x < 0:
        ans = -x * s >> PRECISION
    else:
        ans = x * s >> PRECISION
    return ans
