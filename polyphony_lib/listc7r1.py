# This is calclations for 1d list. Size is fixed.
import float
from polyphony import pipelined, testbench, unroll
from polyphony.typing import List, int8, int32, int64, uint32

LEN = 7
PRECISION = 16


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


def sub_scalar(a: List, b: int32, c: List) -> None:
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


def append(a: List, item: int32, c: List) -> None:
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


def mean(a: List) -> int32:
    s = 0
    for i in unroll(range(LEN)):
        s += a[i]
    return s // LEN



# def linalg_qr(A: List[int32], Q: List[int32], R: List[int32]) -> None:
#     for j in range(ROW):
#         v: List[int32] = [-1] * ROW
#         r_signed: int32 = 0
#         q_signed: int32 = 0
#         a_signed: int32 = 0
#         v_signed: int32 = 0
#         for i in unroll(range(ROW)):
#             v[i] = A[i * COL + j]

#         for i in range(j):
#             R[i * COL + j] = 0
#             for k in range(ROW):
#                 q_signed = Q[k * COL + i]
#                 a_signed = A[k * COL + j]
#                 R[i * COL + j] += float.mult(q_signed, a_signed)
#             v2: List[int32] = [-1] * ROW
#             for k in range(ROW):
#                 q_signed = Q[k * COL + i]
#                 r_signed = R[i * COL + j]
#                 v2[k] = float.mult(q_signed, r_signed)
#             sub(v, v2, v)

#         R[j * COL + j] = linalg_norm(v)
#         for i in unroll(range(ROW)):
#             v_signed = v[i]
#             r_signed = R[j * COL + j]
#             Q[i * COL + j] = float.div(v_signed, r_signed)


def linalg_norm(A: List) -> int32:
    s = 0
    A_signed: int32 = 0
    for i in range(LEN):
        A_signed = A[i]
        A2 = float.mult(A_signed, A_signed)
        s += A2
    # Newton's method
    x = s
    if x <= 0:
        return 0
    for _ in range(10):
        x2 = float.mult(x, x)
        x3 = x2 - s
        x4 = x << 1
        x = x - float.div(x3, x4)
    return x
