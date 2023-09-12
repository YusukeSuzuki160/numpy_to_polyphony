# This is calclations for list. Size is fixed.

from polyphony import pipelined, testbench, unroll
from polyphony.typing import List, int32

ROW = 3
COL = 3
LEN = ROW * COL


def add(a: List, b: List, c: List):
    for i in unroll(range(LEN)):
        c[i] = a[i] + b[i]


def matmult(a: List, b: List, col, c: List):
    for i in range(col):
        for j in range(ROW):
            for k in unroll(range(COL)):
                c[i * COL + j] += a[i * COL + k] * b[k * COL + j]


# def sqrt(a: List, c: List):
#     # Newton's method
#     for i in unroll(range(LEN)):
#         x = a[i]
#         for _ in range(10):
#             x = x - (x * x - a[i]) / (2 * x)
#         c[i] = x


def append(a: List, item: int32, c: List):
    for i in unroll(range(LEN)):
        c[i] = a[i]
    c[len(a)] = item


def argsort(a: List, c: List):
    for i in range(COL):
        for j in unroll(range(ROW)):
            c[i * COL + j] = j
    for i in range(ROW):
        for j in range(COL):
            for k in range(COL - 1):
                if a[i * COL + c[i * COL + k]] > a[i * COL + c[i * COL + k + 1]]:
                    c[i * COL + k], c[i * COL + k + 1] = c[i * COL + k + 1], c[i * COL + k]

# def cov(a: List, rowvar, c: List):
#     if rowvar:
#         for i in range(ROW):
#             for j in range(ROW):
#                 for k in unroll(range(COL)):
#                     c[i * COL + j] += a[k * COL + i] * a[k * COL + j]
#     else:
#         for i in range(ROW):
#             for j in range(ROW):
#                 for k in unroll(range(COL)):
#                     c[i * COL + j] += a[i * COL + k] * a[j * COL + k]


def mean(a: List):
    s = 0
    for i in unroll(range(LEN)):
        s += a[i]
    return s // LEN

def mean_axis_0(a: List, c: List):
    for i in range(ROW):
        for j in unroll(range(COL)):
            c[j] += a[i * COL + j]
    for i in unroll(range(COL)):
        c[i] = c[i] // ROW


# def linalg_eigh(A: List, eigenvalues: List, eigenvectors: List): # can use only symmetric matrix
#     max_iter = 1000
#     tol = 1e-8

#     Q = [0] * (LEN)
#     R = [0] * (LEN)
#     linalg_qr(A, Q, R)
#     V = [0] * (LEN)

#     for i in unroll(range(ROW)):
#         V[i * ROW + i] = 1
#     for _ in range(max_iter):
#         A_new = [0] * (LEN)
#         matmult(R, Q, ROW, A_new)
#         diff = linalg_norm(A_new - A)
#         if diff < tol:
#             break
#         A = A_new
#         Q, R = linalg_qr(A)
#         matmult(V, Q, ROW, V)
#     for i in unroll(range(ROW)):
#         eigenvalues[i] = A[i * ROW + i]
#     for i in range(ROW):
#         for j in unroll(range(ROW)):
#             eigenvectors[i * ROW + j] = V[i * ROW + j]

#     # 固有値を昇順にソート
#     idx = np.argsort(eigenvalues)
#     eigenvalues = eigenvalues[idx]
#     eigenvectors = eigenvectors[:, idx]


# def linalg_qr(A: List, Q: List, R: List):
#     # Q = np.zeros((m, n))
#     # R = np.zeros((n, n))

#     for j in range(ROW):
#         v = A[:, j]

#         for i in range(j):
#             R[i, j] = 0
#             for k in unroll(range(ROW)):
#                 R[i, j] += Q[k, i] * A[k, j]
#             v = v - R[i, j] * Q[:, i]

#         R[j, j] = np.linalg.norm(v)
#         Q[:, j] = v / R[j, j]


# def linalg_norm(A: List):
#     s = 0
#     for i in unroll(range(LEN)):
#         s += A[i] * A[i]
#     # Newton's method
#     x = s
#     for _ in range(10):
#         x = x - (x * x - s) / (2 * x)
#     return x