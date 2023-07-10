import ast 

class Complex(ast.AST):
    def __init__(self, real, imag):
        self.real = real
        self.imag = imag
        self._fields = ('real', 'imag')

class ComplexNumGenerator(ast.NodeTransformer):
    def visit_BinOp(self, node):
        if isinstance(node.left, ast.Num) and isinstance(node.right, ast.Num):
            if isinstance(node.right.n, complex):
                return Complex(node.left, node.right)
        else:
            return node