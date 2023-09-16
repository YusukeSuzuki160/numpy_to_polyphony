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
        if self.is_number(node.left) and self.is_number(node.right):
            if isinstance(self.get_number_node(node.right).n, complex):
                return Complex(node.left, node.right)
        else:
            return node

    def is_number(self, node: Any) -> bool:
        return isinstance(node, ast.Num) or isinstance(node, ast.UnaryOp)

    def get_number_node(self, node: Any) -> Any:
        if isinstance(node, ast.Num):
            return node
        elif isinstance(node, ast.UnaryOp):
            return node.operand
