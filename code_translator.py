from _ast import FunctionDef, List, Name
import ast, astor
from typing import Any
import analyzer
from analyzer import MainArgNameLister, MainCallAnalyzer, TypeAnalyzer
from function_translator import FunctionTranslator

class CodeTranslator(ast.NodeTransformer):
    def __init__(self, code):
        self.npalias = 'np'
        self.code = code
        self.tree = ast.parse(code)
        self.lister = MainArgNameLister()
        self.lister.visit(self.tree)
        self.arg_name_list = self.lister.arg_name_list
        self.main_call_analyzer = MainCallAnalyzer(self.arg_name_list)
        self.main_call_analyzer.visit(self.tree)
        self.array_list = self.main_call_analyzer.array_list
        self.type_analyzer = TypeAnalyzer(self.array_list)
        self.type_analyzer.visit(self.tree)
        self.function_translator = FunctionTranslator(self.array_list, self.type_analyzer.npinstance_list, self.npalias)
        self.function_translator.visit(self.tree)
        self.npinstance_list = self.type_analyzer.npinstance_list
        print(self.npinstance_list)

    def get_npinstance_list(self):
        return self.npinstance_list

    def get_code(self):
        return self.code

    def get_arg_name_list(self):
        return self.arg_name_list

    def get_array_list(self):
        return self.array_list

    def get_tree(self):
        return self.tree

    def get_lister(self):
        return self.lister

    def get_main_call_analyzer(self):
        return self.main_call_analyzer

    def get_type_analyzer(self):
        return self.type_analyzer
    
    def get_func_dict(self):
        return self.function_translator.func_dict

    def flatten_list(self, list_name):
        list_type = self.array_list[list_name]
        shape = list_type['shape']
        length = shape[0] * shape[1]
        list_names = []
        for i in range(length):
            list_names.append(list_name + '_' + str(i))
        return list_names
    def flatten_array(self, array_name):
        array_type = self.array_list[array_name]
        shape = array_type['shape']
        length = shape[0] * shape[1]
        array_names = []
        for i in range(length):
            array_names.append(array_name + '_' + str(i))
        return array_names
    def visit_Name(self, node: Name) -> Any:
        if node.id in self.array_list.keys():
            array_type = self.array_list[node.id]
            shape = array_type['shape']
            length = shape[0] * shape[1]
            return ast.copy_location(ast.Tuple(elts=[ast.Name(id=node.id + '_' + str(i), ctx=ast.Load()) for i in range(length)], ctx=ast.Load()), node)
        elif node.id in self.npinstance_list.keys():
            npinstance_type = self.npinstance_list[node.id]
            shape = npinstance_type['shape']
            length = shape[0] * shape[1]
            return ast.copy_location(ast.Tuple(elts=[ast.Name(id=node.id + '_' + str(i), ctx=ast.Load()) for i in range(length)], ctx=ast.Load()), node)
        return node
    def visit_Call(self, node: ast.Call) -> Any:
        args = []
        for arg in node.args:
            args.append(self.visit(arg))
        ret_args = []
        for arg in args:
            if isinstance(arg, ast.Tuple):
                for elt in arg.elts:
                    ret_args.append(elt)
            else:
                ret_args.append(arg)
        node.args = ret_args
        self.generic_visit(node)
        return node
            
    
    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        ret_args = []
        for arg in args:
            if arg in self.array_list.keys():
                ret_args.extend(self.flatten_list(arg))
            else:
                ret_args.append(arg)
        node.args.args = [ast.arg(arg=arg, annotation=None) for arg in ret_args]
        self.generic_visit(node)
        return node

    def visit_NumpyArray(self, node: ast.Call) -> Any:
        if isinstance(node.args[0], ast.List):
            return ast.copy_location(ast.Tuple(elts=[self.visit(elt) for elt in node.args], ctx=ast.Load()), node)
        elif isinstance(node.args[0], ast.Name):
            return ast.copy_location(ast.Tuple(elts=[self.visit(elt) for elt in node.args], ctx=ast.Load()), node)
    
        
    def visit_List(self, node: List) -> Any:
        args = []
        for elt in node.elts:
            args.append(self.visit(elt))
        ret_args = []
        for arg in args:
            if isinstance(arg, ast.Tuple):
                for elt in arg.elts:
                    ret_args.append(elt)
            else:
                ret_args.append(arg)
        return ast.copy_location(ast.Tuple(elts=ret_args, ctx=ast.Load()), node)
