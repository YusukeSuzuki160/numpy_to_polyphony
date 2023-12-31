import listc14r1 as list_linalg
# This is calclations for list. Size is fixed.
import float
from polyphony import pipelined, testbench, unroll
from polyphony.typing import List, int8, int32, int64, uint32

ROW = 10
COL = 14
LEN = ROW * COL
PRECISION = 24


def transpose(a: List, c: List) -> None:
    for i in range(ROW):
        for j in range(COL):
            c[j * ROW + i] = a[i * COL + j]


def add(a: List, b: List, c: List) -> None:
    for i in unroll(range(LEN)):
        c[i] = a[i] + b[i]


def add_scalar(a: List, b: int32, c: List) -> None:
    for i in unroll(range(LEN)):
        c[i] = a[i] + b


def add_vertical(a: List, b: List, c: List) -> None:
    for i in range(ROW):
        for j in unroll(range(COL)):
            c[i * COL + j] = a[i * COL + j] + b[j]


def add_horizontal(a: List, b: List, c: List) -> None:
    for i in range(ROW):
        for j in unroll(range(COL)):
            c[i * COL + j] = a[i * COL + j] + b[i]


def sub(a: List, b: List, c: List) -> None:
    for i in unroll(range(LEN)):
        c[i] = a[i] - b[i]


def sub_scalar(a: List, b: int32, c: List) -> None:
    for i in unroll(range(LEN)):
        c[i] = a[i] - b


def sub_horizontal(a: List, b: List, c: List) -> None:
    for i in range(ROW):
        for j in unroll(range(COL)):
            c[i * COL + j] = a[i * COL + j] - b[j]


def sub_vertical(a: List, b: List, c: List) -> None:
    for i in range(ROW):
        for j in unroll(range(COL)):
            c[i * COL + j] = a[i * COL + j] - b[i]


def matmult(a: List, b: List, col: int8, c: List) -> None:
    for i in range(col):
        for j in range(COL):
            for k in unroll(range(ROW)):
                a_signed = a[k * COL + j]
                b_signed = b[j * col + i]
                c[k * col + i] += a_signed * b_signed


def matmult_float(a: List, b: List, col: int8, c: List) -> None:
    for i in range(col):
        for j in range(COL):
            for k in unroll(range(ROW)):
                a_signed = a[k * COL + j]
                b_signed = b[j * col + i]
                c[k * col + i] += float.mult(a_signed, b_signed)


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
    for i in range(COL):
        for j in unroll(range(ROW)):
            c[i * COL + j] = j
    for i in range(ROW):
        for j in range(COL):
            for k in range(COL - 1):
                if a[i * COL + c[i * COL + k]] > a[i * COL + c[i * COL + k + 1]]:
                    c[i * COL + k], c[i * COL + k + 1] = c[i * COL + k + 1], c[i * COL + k]


def slice_by_array(a: List, b: List, c: List) -> None:
    for i in range(ROW):
        for j in unroll(range(COL)):
            c[i * COL + j] = a[b[i * COL + j]]


def slice_by_tuple(a: List, b: List, c: List, d: List) -> None:
    for i in range(ROW):
        for j in unroll(range(COL)):
            index = b[i] * COL + c[j]
            d[i * COL + j] = a[index]


def cov(A: List, rowvar: bool, c: List) -> None:
    a = [0] * LEN
    if rowvar == False:
        for i in range(ROW):
            for j in unroll(range(COL)):
                a[i * COL + j] = A[j * ROW + i]
    else:
        for i in unroll(range(LEN)):
            a[i] = A[i]
    a_mean = [0] * ROW
    mean_axis_1(a, a_mean)
    for i in range(ROW):
        for j in unroll(range(COL)):
            a[i * COL + j] -= a_mean[i]
    a_T = [0] * LEN
    transpose(a, a_T)
    matmult_float(a, a_T, ROW, c)
    for i in unroll(range(LEN)):
        c_signed: int32 = c[i]
        c[i] = c_signed // (COL - 1)


def mean(a: List) -> int32:
    s = 0
    for i in unroll(range(LEN)):
        s += a[i]
    return s // LEN


def mean_axis_0(a: List, c: List) -> None:
    for i in range(ROW):
        for j in unroll(range(COL)):
            c[j] += a[i * COL + j]
    for i in unroll(range(COL)):
        c_signed: int32 = c[i]
        c[i] = c_signed // ROW


def mean_axis_1(a: List, c: List) -> None:
    for i in range(COL):
        for j in unroll(range(ROW)):
            c[j] += a[j * COL + i]
    for i in unroll(range(ROW)):
        c_signed: int32 = c[i]
        c[i] = c_signed // COL


def linalg_eigh(
    A: List, eigenvalues: List, eigenvectors: List
) -> None:  # can use only symmetric matrix
    max_iter = 100

    def is_diagonal(m: List) -> bool:
        # 行列が対角であるかのチェック
        for i in range(ROW):
            for j in range(COL):
                m_signed = m[i * COL + j]
                if i != j and (m_signed > 1000 or m_signed < -1000):
                    return False
        return True

    V = [0] * (LEN)

    for i in unroll(range(ROW)):
        V[i * ROW + i] = 65536
    while max_iter > 0:
        Q = [0] * (LEN)
        R = [0] * (LEN)
        linalg_qr(A, Q, R)
        A_new = [0] * (LEN)
        matmult_float(R, Q, ROW, A_new)
        for i in unroll(range(LEN)):
            A[i] = A_new[i]
        V_tmp = [0] * (LEN)
        matmult_float(V, Q, ROW, V_tmp)
        for i in unroll(range(LEN)):
            V[i] = V_tmp[i]
        if is_diagonal(A):
            max_iter = 0
        else:
            max_iter -= 1
    for i in unroll(range(ROW)):
        eigenvalues[i] = A[i * COL + i]
    for i in unroll(range(LEN)):
        eigenvectors[i] = V[i]

    # 固有値を昇順にソート
    idx = [0] * ROW
    list_linalg.argsort(eigenvalues, idx)
    eigenvalues_tmp = [0] * ROW
    list_linalg.slice_by_array(eigenvalues, idx, eigenvalues_tmp)
    for i in unroll(range(ROW)):
        eigenvalues[i] = eigenvalues_tmp[i]
    indexes = [0] * ROW
    for i in unroll(range(ROW)):
        indexes[i] = i
    eigenvectors_tmp = [0] * LEN
    slice_by_tuple(eigenvectors, indexes, idx, eigenvectors_tmp)
    for i in unroll(range(LEN)):
        eigenvectors[i] = eigenvectors_tmp[i]


def linalg_qr(A: List[int32], Q: List[int32], R: List[int32]) -> None:
    for j in range(COL):
        v: List[int32] = [0] * ROW
        r_signed: int32 = 0
        q_signed: int32 = 0
        v_signed: int32 = 0
        for i in unroll(range(ROW)):
            v[i] = A[i * COL + j]
        for i in range(j):
            R[i * COL + j] = 0
            for k in range(ROW):
                q_signed = Q[k * COL + i]
                v_signed = v[k]
                R[i * COL + j] += float.mult(q_signed, v_signed)
        v2: List[int32] = [0] * ROW
        for i in range(j):
            for k in range(ROW):
                q_signed = Q[k * COL + i]
                r_signed = R[i * COL + j]
                v2[k] = float.mult(q_signed, r_signed)
            list_linalg.sub(v, v2, v)
        norm_v = list_linalg.linalg_norm(v)
        if norm_v == 0:
            continue
        else:
            R[j * COL + j] = norm_v
            for i in unroll(range(ROW)):
                v_signed = v[i]
                r_signed = R[j * COL + j]
                Q[i * COL + j] = float.div(v_signed, r_signed)


def linalg_norm(A: List) -> int32:
    s: int32 = 0
    A_signed: int32 = 0
    for i in range(LEN):
        A_signed = A[i]
        A2 = float.mult(A_signed, A_signed)
        s += A2
    # Newton's method
    x: int64 = s
    count = 100
    while count > 0:
        x2: int64 = x * x >> PRECISION
        x3: int64 = (x2 - s) << PRECISION
        x4: int64 = x << 1
        x5: int64 = x3 // x4
        if x5 < 10 and x5 > -10:
            count = 0
        else:
            count -= 1
            x -= x5
    return x
