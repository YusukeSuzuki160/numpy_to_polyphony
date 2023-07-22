from _ast import Call, FunctionDef, Import, Return
import ast
from typing import Any
import struct

class ReturnAnalyzer(ast.NodeVisitor):
    def __init__(self, array_list, float_list, complex_list, np_list):
        self.array_list = array_list
        self.float_list = float_list
        self.complex_list = complex_list
        self.np_list = np_list
        self.returns = {}
        self.function_stack = []
    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.function_stack.append(node.name)
        self.generic_visit(node)
    def visit_Return(self, node: Return) -> Any:
        returns = []
        if isinstance(node.value, ast.Name):
            returns.append(node.value.id)
        elif isinstance(node.value, ast.Tuple):
            for value in node.value.elts:
                if isinstance(value, ast.Name):
                    returns.append(value.id)
        func_name = self.function_stack.pop()
        self.returns[func_name] = returns
    

class LastTranslator(ast.NodeTransformer):
    def __init__(self, arrat_list, float_list, complex_list, np_list, returns):
        self.precision = 16
        self.array_list = arrat_list
        self.float_list = float_list
        self.complex_list = complex_list
        self.np_list = np_list
        self.returns = returns
        self.add_args = {}
        self.func_stack = []

    def visit(self, node):
        return super().visit(node)

    def visit_Import(self, node: Import) -> Any:
        if node.names[0].name == 'numpy':
            return None
        else:
            return node
    
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
        self.func_stack.append(node.name)
        new_args = []
        for arg in node.args.args:
            arg_name = arg.arg
            if arg_name.split('_')[0] in self.array_list.keys():
                dtype = self.array_list[arg_name.split('_')[0]]['dtype']
                if dtype == 'complex128':
                    dtype = 'int64'
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

        if node.name in self.returns.keys():
            returns = self.returns[node.name]
            for ret in returns:
                raw_name = ret.split('_')[0]
                if raw_name in self.array_list.keys():
                    dtype = self.array_list[raw_name]['dtype']
                    if dtype == 'complex128':
                        dtype = 'int64'
                    elif dtype == 'complex64':
                        dtype = 'int32'
                    elif dtype == 'float64':
                        dtype = 'int64'
                    elif dtype == 'float32':
                        dtype = 'int32'
                elif raw_name in self.np_list.keys():
                    dtype = self.np_list[raw_name]['dtype']
                    if dtype == 'complex128':
                        dtype = 'int64'
                    elif dtype == 'complex64':
                        dtype = 'int32'
                    elif dtype == 'float64':
                        dtype = 'int64'
                    elif dtype == 'float32':
                        dtype = 'int32'
                elif raw_name in self.float_list.keys():
                    bit = self.float_list[raw_name].split('fixed')[1]
                    dtype = 'int' + bit
                elif raw_name in self.complex_list.keys():
                    bit = str(int(self.complex_list[raw_name].split('complex')[1]) // 2)
                    dtype = 'int' + bit
                else:
                    dtype = 'int32'
                new_args.append(ast.arg(arg=ret, annotation=ast.Name(id=dtype, ctx=ast.Load())))
        node.args.args = new_args
        self.generic_visit(node)
        return node
    
    def visit_Assign(self, node):
        if isinstance(node.value, ast.Call):
            # print(ast.dump(node))
            if isinstance(node.value.func, ast.Attribute):
                func_name = node.value.func.attr
            else:
                func_name = node.value.func.id
            if func_name in self.returns.keys():
                node = node.value
                returns = self.returns[func_name]
                self.add_args[self.func_stack[-1]] = []
                for ret in returns:
                    node.args.append(ast.Name(id=ret, ctx=ast.Load()))
                    self.add_args[self.func_stack[-1]].append(ret)
                self.generic_visit(node)
                return ast.Expr(value=node)
        
        self.generic_visit(node)
        return node
    
    
    def visit_Return(self, node: Return) -> Any:
        self.func_stack.pop()
        return None

    
    def fixed_to_int(self, number):
        return int(number * (1 << self.precision))
    

class AddArgsDifinition(ast.NodeTransformer):
    def __init__(self, add_args) -> None:
        self.add_args = add_args
        super().__init__()

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        args_difinitnion = []
        func_name = node.name
        if func_name in self.add_args.keys():
            for arg in self.add_args[func_name]:
                args_difinitnion.append(ast.Assign(targets=[ast.Name(id=arg, ctx=ast.Store())], value=ast.Name(id='0', ctx=ast.Load())))
        node.body = args_difinitnion + node.body
        return node