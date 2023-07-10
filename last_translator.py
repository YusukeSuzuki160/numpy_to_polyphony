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
    
    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        new_args = []
        for arg in node.args.args:
            arg_name = arg.arg
            if arg_name.split('_')[0] in self.array_list.keys():
                dtype = self.array_list[arg_name.split('_')[0]]['dtype']
                new_args.append(ast.arg(arg=arg_name, annotation=ast.Name(id=dtype, ctx=ast.Load())))
            elif arg_name in self.float_list.keys():
                bit = self.float_list[arg_name].split('fixed')[1]
                int_type = 'int' + bit
                new_args.append(ast.arg(arg=arg_name, annotation=ast.Name(id=int_type, ctx=ast.Load())))
            elif arg_name in self.complex_list.keys():
                bit = str(int(self.complex_list[arg_name].split('complex')[1]) // 2)
                int_type = 'int' + bit
                new_args.append(ast.arg(arg=arg_name + '_real', annotation=ast.Name(id=int_type, ctx=ast.Load())))
                new_args.append(ast.arg(arg=arg_name + '_imag', annotation=ast.Name(id=int_type, ctx=ast.Load())))
            else:
                new_args.append(arg)

        node.args.args = new_args
        self.generic_visit(node)
        return node

    
    def fixed_to_int(self, number):
        return int(number * (1 << self.precision))