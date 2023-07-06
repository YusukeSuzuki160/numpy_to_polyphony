from _ast import Assign, FunctionDef
import ast
from typing import Any

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
        self.main_args = arg_name_list

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == 'main':
            i = 0
            for arg in node.args:
                if isinstance(arg, ast.List):
                    arg_name = node.func.id + '_arg' + str(i)
                    append_dict = {}
                    append_dict['shape'] = get_shape_from_list(arg)
                    element = arg.elts[0]
                    while isinstance(element, ast.List):
                        element = element.elts[0]
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
                    i += 1
        self.generic_visit(node)



class TypeAnalyzer(ast.NodeVisitor):
    def __init__(self, arg_name_list):
        self.array_list = arg_name_list
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
                            if isinstance(node.value.args[0], ast.Name):
                                arg_name = node.targets[0].id
                                append_dict = {}
                                append_dict = self.array_list[node.value.args[0].id]
                                if node.value.keywords != []:
                                    if node.value.keywords[0].arg == 'dtype':
                                        dtype = node.value.keywords[0].value.attr
                                        append_dict['dtype'] = dtype
                                self.npinstance_list[arg_name] = append_dict
        elif isinstance(node.value, ast.BinOp):
            self.visit(node.value)
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