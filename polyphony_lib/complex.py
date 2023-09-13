PRECISION = 16
from polyphony.typing import int64


def mult(a: int64, b: int64) -> int64:
    a_real: int64 = (a >> 32) & 0xFFFFFFFF
    a_imag: int64 = a & 0xFFFFFFFF
    b_real: int64 = (b >> 32) & 0xFFFFFFFF
    b_imag: int64 = b & 0xFFFFFFFF
    c_real: int64 = (a_real * b_real - a_imag * b_imag) >> PRECISION
    c_imag: int64 = (a_real * b_imag + a_imag * b_real) >> PRECISION
    return (c_real << 32) | c_imag
