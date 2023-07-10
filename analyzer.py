from _ast import Assign, FunctionDef, Return
import ast, astor
from typing import Any
from parse_complex import Complex

def get_shape_from_list(list_node):
        if isinstance(list_node, ast.List):
            return [len(list_node.elts)] + get_shape_from_list(list_node.elts[0])
        else:
            return []

class MainArgNameLister(ast.NodeVisitor):
    def __init__(self):
        self.arg_name_list = {}
        self.current_arg = 0
    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        if node.name == 'main':
            for arg in node.args.args:
                arg_name = 'main_arg' + str(self.current_arg)
                self.arg_name_list[arg_name] = arg.arg
                self.current_arg += 1
        self.generic_visit(node)

class MainCallAnalyzer(ast.NodeVisitor):
    def __init__(self, arg_name_list):
        self.array_list = {}
        self.float_list = {}
        self.complex_list = {}
        self.main_args = arg_name_list

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == 'main':
            i = 0
            for arg in node.args:
                if isinstance(arg, ast.List):
                    arg_name = node.func.id + '_arg' + str(i)
                    append_dict = {}
                    shape = get_shape_from_list(arg)
                    if len(shape) == 1:
                        shape = [1] + shape
                    append_dict['shape'] = shape
                    element = arg.elts[0]
                    while isinstance(element, ast.List):
                        element = element.elts[0]
                    if isinstance(element, Complex):
                        dtype = 'complex128'
                    else:
                        dtype = type(element.n)
                        if dtype == int:
                            dtype = 'int64'
                        elif dtype == float:
                            dtype = 'float64'
                        elif dtype == bool:
                            dtype = 'bool'
                        elif dtype == complex:
                            dtype = 'complex128'
                        else:
                            dtype = 'object'
                    append_dict['dtype'] = dtype
                    self.array_list[self.main_args[arg_name]] = append_dict
                    if dtype == 'float64':
                        length = shape[0] * shape[1]
                        for j in range(length):
                            self.float_list[self.main_args[arg_name] + '_' + str(j)] = 'fixed64'
                    elif dtype == 'complex128':
                        length = shape[0] * shape[1]
                        for j in range(length):
                            self.complex_list[self.main_args[arg_name] + '_' + str(j)] = 'complex128'
                    i += 1
                elif isinstance(arg, ast.Num):
                    if type(arg.n) == float:
                        self.float_list[self.main_args['main_arg' + str(i)]] = 'fixed64'
                    i += 1
                elif isinstance(arg, Complex):
                    self.complex_list[self.main_args['main_arg' + str(i)]] = 'complex128'
                    i += 1
        self.generic_visit(node)
    def visit_Assign(self, node: Assign) -> Any:
        if isinstance(node.value, ast.List):
            arg_name = node.targets[0].id
            append_dict = {}
            shape = get_shape_from_list(node.value)
            if len(shape) == 1:
                shape = [1] + shape
            append_dict['shape'] = shape
            element = node.value.elts[0]
            while isinstance(element, ast.List):
                element = element.elts[0]
            if isinstance(element, Complex):
                dtype = 'complex128'
            else: 
                dtype = type(element.n)
                if dtype == int:
                    dtype = 'int64'
                elif dtype == float:
                    dtype = 'float64'
                elif dtype == bool:
                    dtype = 'bool'
                elif dtype == complex:
                    dtype = 'complex128'
                else:
                    dtype = 'object'
            append_dict['dtype'] = dtype
            self.array_list[arg_name] = append_dict
            if dtype == 'float64':
                length = shape[0] * shape[1]
                for j in range(length):
                    self.float_list[self.main_args[arg_name] + '_' + str(j)] = 'fixed64'
            elif dtype == 'complex128':
                length = shape[0] * shape[1]
                for j in range(length):
                    self.complex_list[self.main_args[arg_name] + '_' + str(j)] = 'complex128'
        self.generic_visit(node)



class TypeAnalyzer(ast.NodeVisitor):
    def __init__(self, arg_name_list, float_list, complex_list):
        self.array_list = arg_name_list
        self.float_list = float_list
        self.complex_list = complex_list
        self.npinstance_list = {}

    def visit_Assign(self, node: Assign) -> Any:
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Attribute):
                if node.value.func.attr == 'array':
                    if isinstance(node.value.func.value, ast.Name):
                        if node.value.func.value.id == 'np':
                            if isinstance(node.value.args[0], ast.List):
                                arg_name = node.targets[0].id
                                append_dict = {}
                                append_dict['shape'] = get_shape_from_list(node.value.args[0])
                                element = node.value.args[0].elts[0]
                                while isinstance(element, ast.List):
                                    element = element.elts[0]
                                if isinstance(element, Complex):
                                    dtype = 'complex128'
                                else:
                                    dtype = type(element.n)
                                    if dtype == int:
                                        dtype = 'int64'
                                    elif dtype == float:
                                        dtype = 'float64'
                                    elif dtype == bool:
                                        dtype = 'bool'
                                    elif dtype == complex:
                                        dtype = 'complex128'
                                    else:
                                        dtype = 'object'
                                if node.value.keywords != []:
                                    if node.value.keywords[0].arg == 'dtype':
                                        dtype = node.value.keywords[0].value.value.id
                                append_dict['dtype'] = dtype
                                self.npinstance_list[arg_name] = append_dict
                                if dtype == 'float64':
                                    length = shape[0] * shape[1]
                                    for j in range(length):
                                        self.float_list[arg_name + '_' + str(j)] = 'fixed64'
                                elif dtype == 'complex128':
                                    length = shape[0] * shape[1]
                                    for j in range(length):
                                        self.complex_list[arg_name + '_' + str(j)] = 'complex128'
                            if isinstance(node.value.args[0], ast.Name):
                                arg_name = node.targets[0].id
                                append_dict = {}
                                append_dict = self.array_list[node.value.args[0].id]
                                dtype = append_dict['dtype']
                                if node.value.keywords != []:
                                    if node.value.keywords[0].arg == 'dtype':
                                        dtype = node.value.keywords[0].value.attr
                                        append_dict['dtype'] = dtype
                                self.npinstance_list[arg_name] = append_dict
                                shape = append_dict['shape']
                                length = shape[0] * shape[1]
                                for j in range(length):
                                    self.complex_list[arg_name + '_' + str(j)] = 'complex128'
                elif node.value.func.attr == 'fft':
                    if isinstance(node.value.func.value.value, ast.Name):
                        if node.value.func.value.value.id == 'np':
                            if isinstance(node.value.args[0], ast.Name):
                                arg_name = node.targets[0].id
                                append_dict = {}
                                append_dict = self.npinstance_list[node.value.args[0].id]
                                append_dict['dtype'] = 'complex128'
                                shape = append_dict['shape']
                                length = shape[0] * shape[1]
                                for j in range(length):
                                    self.complex_list[arg_name + '_' + str(j)] = 'complex128'
                                self.npinstance_list[arg_name] = append_dict
                
        elif isinstance(node.value, ast.Name):
            if node.value.id in self.npinstance_list:
                self.npinstance_list[node.targets[0].id] = self.npinstance_list[node.value.id]
            elif node.value.id in self.float_list:
                self.float_list[node.targets[0].id] = self.float_list[node.value.id]
            elif node.value.id in self.complex_list:
                self.complex_list[node.targets[0].id] = self.complex_list[node.value.id]
        elif isinstance(node.value, ast.BinOp):
            self.visit(node.value)
            if node.value.left.id not in self.npinstance_list:
                if node.value.left.id in self.float_list:
                    self.float_list[node.targets[0].id] = self.float_list[node.value.left.id]
                    self.generic_visit(node)
                    return
                elif node.value.left.id in self.complex_list:
                    self.complex_list[node.targets[0].id] = self.complex_list[node.value.left.id]
                    self.generic_visit(node)
                    return
            left_type = self.npinstance_list[node.value.left.id]['dtype']
            right_type = self.npinstance_list[node.value.right.id]['dtype']
            assert left_type == right_type
            left_shape = self.npinstance_list[node.value.left.id]['shape']
            right_shape = self.npinstance_list[node.value.right.id]['shape']
            dtype = left_type
            append_dict = {}
            if isinstance(node.value.op, ast.Add) or isinstance(node.value.op, ast.Sub) or isinstance(node.value.op, ast.Mult):
                shape = left_shape
                assert shape == right_shape # TODO: broadcast
                append_dict['shape'] = shape
            elif isinstance(node.value.op, ast.MatMult):
                shape = [left_shape[0], right_shape[1]]
                assert left_shape[1] == right_shape[0]
                append_dict['shape'] = shape
            append_dict['dtype'] = dtype
            self.npinstance_list[node.targets[0].id] = append_dict
        elif isinstance(node.value, ast.UnaryOp):
            self.visit(node.value)
            dtype = self.npinstance_list[node.value.operand.id]['dtype']
            append_dict = {}
            append_dict['dtype'] = dtype
            append_dict['shape'] = self.npinstance_list[node.value.operand.id]['shape']
            self.npinstance_list[node.targets[0].id] = append_dict
        elif isinstance(node.value, ast.Subscript):
            self.visit(node.value)
            dtype = self.npinstance_list[node.value.value.id]['dtype']
            append_dict = {}
            append_dict['dtype'] = dtype
            append_dict['shape'] = self.npinstance_list[node.value.value.id]['shape'][1:]
            self.npinstance_list[node.targets[0].id] = append_dict
        self.generic_visit(node)


class FunctionAnalyzer(ast.NodeVisitor):
    def __init__(self, array_list, float_list, complex_list, np_list):
        self.array_list = array_list
        self.float_list = float_list
        self.complex_list = complex_list
        self.np_list = np_list
        self.func_return = {}
    
    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        if isinstance(node.body[-1], ast.Return):
            func_name = node.name
            return_id = node.body[-1].value.id
            if return_id in self.np_list:
                self.func_return[func_name] = self.np_list[return_id]
            elif return_id in self.float_list:
                self.func_return[func_name] = self.float_list[return_id]
            elif return_id in self.complex_list:
                self.func_return[func_name] = self.complex_list[return_id]
            elif return_id in self.array_list:
                self.func_return[func_name] = self.array_list[return_id]
        self.generic_visit(node)

class FunctionCallAnalyzer(ast.NodeVisitor):
    def __init__(self, array_list, float_list, complex_list, np_list, func_return):
        self.array_list = array_list
        self.float_list = float_list
        self.complex_list = complex_list
        self.np_list = np_list
        self.func_return = func_return
    
    def visit_Assign(self, node):
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                if node.value.func.id in self.func_return.keys():
                    dist_name = node.targets[0].id
                    src_type = self.func_return[node.value.func.id]
                    if isinstance(src_type, dict):
                        self.np_list[dist_name] = src_type
                    elif isinstance(src_type, str):
                        if 'fixed' in src_type:
                            self.float_list[dist_name] = src_type
                        elif 'complex' in src_type:
                            self.complex_list[dist_name] = src_type
        
        self.generic_visit(node)
