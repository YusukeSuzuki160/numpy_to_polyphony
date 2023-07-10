from _ast import Call
import ast, astor
from typing import Any, Set

class FunctionTranslator(ast.NodeTransformer):
    def __init__(self, array_list, np_list, float_list, complex_list, np_alias='np'):
        self.array_list = array_list
        self.np_list = np_list
        self.float_list = float_list
        self.complex_list = complex_list
        self.np_alias = np_alias
        self.func_dict = {}
    
    def visit_Call(self, node: Call) -> Any:
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'np':
                if node.func.attr == 'array':
                    if isinstance(node.args[0], ast.Name):
                        if node.args[0].id in self.array_list.keys():
                            shape = self.array_list[node.args[0].id]['shape']
                            length = shape[0] * shape[1]
                            dtype = self.array_list[node.args[0].id]['dtype']
                            self.func_dict[node.func.attr] = {'shape': shape, 'dtype': dtype}
                            function_name = node.func.attr + '_' + str(length) + '_' + self.array_list[node.args[0].id]['dtype']
                            return ast.copy_location(ast.Call(func=ast.Attribute(value=ast.Name(id=self.np_alias, ctx=ast.Load()), attr=function_name, ctx=ast.Load()), args=node.args, keywords=[]), node)
                elif node.func.attr == 'array_equal':
                    left = node.args[0]
                    right = node.args[1]
                    if isinstance(left, ast.Name) and isinstance(right, ast.Name):
                        if left.id in self.array_list.keys() and right.id in self.array_list.keys():
                            shape = self.array_list[left.id]['shape']
                            length = shape[0] * shape[1]
                            self.func_dict[node.func.attr] = {'shape': shape, 'dtype': self.array_list[left.id]['dtype']}
                            function_name = node.func.attr + '_' + str(length) + '_' + self.array_list[left.id]['dtype']
                            return ast.copy_location(ast.Call(func=ast.Attribute(value=ast.Name(id=self.np_alias, ctx=ast.Load()), attr=function_name, ctx=ast.Load()), args=node.args, keywords=[]), node)
                        elif left.id in self.np_list.keys() and right.id in self.np_list.keys():
                            shape = self.np_list[left.id]['shape']
                            length = shape[0] * shape[1]
                            self.func_dict[node.func.attr] = {'shape': shape, 'dtype': self.np_list[left.id]['dtype']}
                            function_name = node.func.attr + '_' + str(length) + '_' + self.np_list[left.id]['dtype']
                            return ast.copy_location(ast.Call(func=ast.Attribute(value=ast.Name(id=self.np_alias, ctx=ast.Load()), attr=function_name, ctx=ast.Load()), args=node.args, keywords=[]), node)
            elif isinstance(node.func.value, ast.Attribute) and node.func.value.value.id == 'np':
                if node.func.attr == 'fft':
                    if isinstance(node.args[0], ast.Name):
                        if node.args[0].id in self.array_list.keys():
                            shape = self.array_list[node.args[0].id]['shape']
                            length = shape[0] * shape[1]
                            self.func_dict[node.func.attr] = {'shape': shape, 'dtype': self.array_list[node.args[0].id]['dtype']}
                            function_name = node.func.attr + '_' + str(length) + '_' + self.array_list[node.args[0].id]['dtype']
                            return ast.copy_location(ast.Call(func=ast.Attribute(value=ast.Name(id=self.np_alias, ctx=ast.Load()), attr=function_name, ctx=ast.Load()), args=node.args, keywords=[]), node)
                        elif node.args[0].id in self.np_list.keys():
                            shape = self.np_list[node.args[0].id]['shape']
                            self.func_dict[node.func.attr] = {'shape': shape, 'dtype': self.np_list[node.args[0].id]['dtype']}
                            function_name = node.func.attr + '_' + str(shape[0]) + '_' + str(shape[1]) + '_' + self.np_list[node.args[0].id]['dtype']
                            return ast.copy_location(ast.Call(func=ast.Attribute(value=ast.Name(id=self.np_alias, ctx=ast.Load()), attr=function_name, ctx=ast.Load()), args=node.args, keywords=[]), node)
                        
        elif isinstance(node.func, ast.Name) and node.func.id == 'print': # print => np.print
            if node.args[0].id not in self.np_list.keys():
                if node.args[0].id in self.complex_list.keys():
                    dtype = self.complex_list[node.args[0].id]
                    function_name = '_print_' + dtype
                    self.func_dict[function_name] = {'dtype': dtype}
                    return ast.Call(func=ast.Attribute(value=ast.Name(id='np', ctx=ast.Load()), attr=function_name, ctx=ast.Load()), args=node.args, keywords=[], starargs=None, kwargs=None)
            shape = self.np_list[node.args[0].id]['shape']
            dtype = self.np_list[node.args[0].id]['dtype']
            function_name = '_print_' + str(shape[0] * shape[1]) + '_' + dtype
            self.func_dict[function_name] = {'shape': shape, 'dtype': dtype}
            return ast.Call(func=ast.Attribute(value=ast.Name(id='np', ctx=ast.Load()), attr=function_name, ctx=ast.Load()), args=node.args, keywords=[], starargs=None, kwargs=None)
        else:
            return node
                    
    def visit_BinOp(self, node: ast.BinOp) -> Any:
        left = node.left
        right = node.right
        if left.id not in self.np_list.keys() or right.id not in self.np_list.keys():
            if left.id in self.float_list.keys() and right.id in self.float_list.keys():
                return self.flaot_to_int(node)
            elif left.id in self.complex_list.keys() and right.id in self.complex_list.keys():
                return self.complex_to_int(node)
            else:
                return node
        if isinstance(left, ast.Name) and isinstance(right, ast.Name):
            left_shape = self.np_list[left.id]['shape']
            right_shape = self.np_list[right.id]['shape']
        dtype = self.np_list[left.id]['dtype']
        function_name = ''
        args = [left, right]
        if isinstance(node.op, ast.Add):
            function_name = 'add'
        elif isinstance(node.op, ast.Sub):
            function_name = 'sub'
        elif isinstance(node.op, ast.Mult):
            function_name = 'mult'
        elif isinstance(node.op, ast.MatMult):
            function_name = 'matmult'
        if function_name != '':
            self.func_dict[function_name] = {'shape1': left_shape, 'shape2': right_shape, 'dtype': dtype}
            shapes = '_' + 'l' + str(left_shape[0]) + '_' + str(left_shape[1]) + '_' + 'r' + str(right_shape[0]) + '_' + str(right_shape[1])
            function_name = function_name + shapes + '_' + dtype
            return ast.copy_location(ast.Call(func=ast.Attribute(value=ast.Name(id=self.np_alias, ctx=ast.Load()), attr=function_name, ctx=ast.Load()), args=args, keywords=[]), node)
        
    def flaot_to_int(self, node: ast.BinOp) -> Any:
        function_name = ''
        dtype = self.float_list[node.left.id]
        if isinstance(node.op, ast.Add):
            function_name = dtype + '_add'
        elif isinstance(node.op, ast.Sub):
            function_name = dtype + '_sub'
        elif isinstance(node.op, ast.Mult):
            function_name = dtype + '_mult'

        if function_name != '':
            self.func_dict[function_name] = {'dtype': dtype}
            return ast.copy_location(ast.Call(func=ast.Attribute(value=ast.Name(id=self.np_alias, ctx=ast.Load()), attr=function_name, ctx=ast.Load()), args=[node.left, node.right], keywords=[]), node)
        
    def complex_to_int(self, node):
        function_name = ''
        dtype = self.complex_list[node.left.id]
        if isinstance(node.op, ast.Add):
            function_name = dtype + '_add'
        elif isinstance(node.op, ast.Sub):
            function_name = dtype + '_sub'
        elif isinstance(node.op, ast.Mult):
            function_name = dtype + '_mult'

        if function_name != '':
            self.func_dict[function_name] = {'dtype': dtype}
            return ast.copy_location(ast.Call(func=ast.Attribute(value=ast.Name(id=self.np_alias, ctx=ast.Load()), attr=function_name, ctx=ast.Load()), args=[node.left, node.right], keywords=[]), node)