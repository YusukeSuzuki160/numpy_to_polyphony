from _ast import Call
import ast
from typing import Any, Set

class FunctionTranslator(ast.NodeTransformer):
    def __init__(self, array_list, np_list, np_alias='np'):
        self.array_list = array_list
        self.np_list = np_list
        self.np_alias = np_alias
        self.func_dict = {}
    
    def visit_Call(self, node: Call) -> Any:
        if isinstance(node.func, ast.Attribute) and node.func.value.id == 'np':
            if node.func.attr == 'array':
                if isinstance(node.args[0], ast.Name):
                    if node.args[0].id in self.array_list.keys():
                        shape = self.array_list[node.args[0].id]['shape']
                        length = shape[0] * shape[1]
                        self.func_dict[node.func.attr] = {'shape': shape, 'dtype': self.array_list[node.args[0].id]['dtype']}
                        function_name = node.func.attr + '_' + str(length) + '_' + self.array_list[node.args[0].id]['dtype']
                        return ast.copy_location(ast.Call(func=ast.Attribute(value=ast.Name(id=self.np_alias, ctx=ast.Load()), attr=function_name, ctx=ast.Load()), args=node.args, keywords=[]), node)
        elif isinstance(node.func, ast.Name) and node.func.id == 'print': # print => np.print
            shape = self.np_list[node.args[0].id]['shape']
            dtype = self.np_list[node.args[0].id]['dtype']
            self.func_dict['print'] = {'shape': shape, 'dtype': dtype}
            function_name = '_print_' + str(shape[0] * shape[1]) + '_' + dtype
            return ast.Call(func=ast.Attribute(value=ast.Name(id='np', ctx=ast.Load()), attr=function_name, ctx=ast.Load()), args=node.args, keywords=[], starargs=None, kwargs=None)
        else:
            return node
                    
    def visit_BinOp(self, node: ast.BinOp) -> Any:
        left = node.left
        right = node.right
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