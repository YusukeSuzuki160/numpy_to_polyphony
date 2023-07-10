from _ast import FunctionDef, Import
import ast
from typing import Any
import struct

class LastTranslator(ast.NodeTransformer):
    def __init__(self, arrat_list, float_list, complex_list, np_list):
        self.precision = 16
        self.array_list = arrat_list
        self.float_list = float_list
        self.complex_list = complex_list
        self.np_list = np_list
    def visit_Import(self, node: Import) -> Any:
        if node.names[0].name == 'numpy':
            return ast.ImportFrom(module='polyphony', names=[ast.alias(name='numpy', asname='np')], level=0)
    
    def visit_Num(self, node):
        if type(node.n) == float:
            num = self.fixed_to_int(node.n)
            return ast.Num(n=num)
        elif type(node.n) == complex:
            imag = node.n.imag
            if type(imag) == float:
                imag = self.fixed_to_int(imag)
            return ast.Num(n=imag)
        else:
            return node

    
    def fixed_to_int(self, number):
        return int(number * (1 << self.precision))