import ast 

class Complex(ast.AST):
    def __init__(self, real, imag):
        self.real = real
        self.imag = imag
        self._fields = ('real', 'imag')

class ComplexNumGenerator(ast.NodeTransformer):
    def visit_BinOp(self, node):
        if self.is_number(node.left) and self.is_number(node.right):
            if isinstance(self.get_number_node(node.right).n, complex):
                return Complex(node.left, node.right)
        else:
            return node
    def is_number(self, node):
        return isinstance(node, ast.Num) or isinstance(node, ast.UnaryOp)

    def get_number_node(self, node):
        if isinstance(node, ast.Num):
            return node
        elif isinstance(node, ast.UnaryOp):
            return node.operand
    
