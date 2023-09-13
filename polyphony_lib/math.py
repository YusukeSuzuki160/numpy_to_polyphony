from polyphony import testbench, pure
import float

PRECISION = 16

@pure
def fixed(a):
    return int(a * (1 << PRECISION))

two = fixed(2)
cycle = 10

def pow(a, n):
    c = 1
    for i in range(n):
        c = c * a
    return c

def sqrt(a): # Newton's method
    x = a
    for _ in range(cycle):
        x = float.div(x + float.div(a, x), two)
    return x

@testbench
def test():
    a = fixed(2)
    b = sqrt(a)
    print(b)
    c = fixed(4)
    d = sqrt(c)
    print(d)
    e = 8
    f = pow(e, 2)
    print(f)
test()
