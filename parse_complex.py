# Standard Library
import ast
from _ast import BinOp
from typing import Any


class Complex(ast.AST):
    def __init__(self, real: ast.Num, imag: ast.Num) -> None:
        self.real = real
        self.imag = imag


class ComplexNumGenerator(ast.NodeTransformer):
    def visit_BinOp(self, node: BinOp) -> Any:
        if isinstance(node.left, ast.Num) and isinstance(node.right, ast.Num):
            if isinstance(node.right.n, complex):
                return Complex(node.left, node.right)
        else:
            return node
