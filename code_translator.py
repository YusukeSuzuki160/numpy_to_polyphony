from _ast import FunctionDef, List, Name
import ast, astor
from typing import Any
import analyzer
from analyzer import MainArgNameLister, MainCallAnalyzer, TypeAnalyzer, FunctionAnalyzer, FunctionCallAnalyzer
from function_translator import FunctionTranslator
from parse_complex import Complex, ComplexNumGenerator

class CodeTranslator(ast.NodeTransformer):
    def __init__(self, code):
        self.npalias = 'np'
        self.code = code
        self.tree = ast.parse(code)
        self.complex_parser = ComplexNumGenerator()
        self.complex_parser.visit(self.tree)
        self.lister = MainArgNameLister()
        self.lister.visit(self.tree)
        self.arg_name_list = self.lister.arg_name_list
        self.main_call_analyzer = MainCallAnalyzer(self.arg_name_list)
        self.main_call_analyzer.visit(self.tree)
        self.array_list = self.main_call_analyzer.array_list
        self.float_list = self.main_call_analyzer.float_list
        self.complex_list = self.main_call_analyzer.complex_list
        self.type_analyzer = TypeAnalyzer(self.array_list, self.float_list, self.complex_list)
        self.type_analyzer.visit(self.tree)
        self.function_analyzer = FunctionAnalyzer(self.array_list, self.type_analyzer.float_list, self.type_analyzer.complex_list, self.type_analyzer.npinstance_list)
        self.function_analyzer.visit(self.tree)
        self.function_call_analyzer = FunctionCallAnalyzer(self.function_analyzer.array_list, self.function_analyzer.float_list, self.function_analyzer.complex_list, self.function_analyzer.np_list, self.function_analyzer.func_return)
        self.function_call_analyzer.visit(self.tree)
        self.function_translator = FunctionTranslator(self.array_list, self.function_call_analyzer.np_list, self.function_call_analyzer.float_list, self.function_call_analyzer.complex_list, self.npalias)
        self.function_translator.visit(self.tree)
        self.npinstance_list = self.function_analyzer.np_list

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
    
    def get_float_list(self):
        return self.type_analyzer.float_list
    
    def get_complex_list(self):
        return self.type_analyzer.complex_list

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
            dtype = array_type['dtype']
            if dtype == 'complex128':
                elts = []
                for i in range(length):
                    elts.append(ast.Name(id=node.id + '_' + str(i) + '_real', ctx=ast.Load()))
                    elts.append(ast.Name(id=node.id + '_' + str(i) + '_imag', ctx=ast.Load()))
            else:
                elts = [ast.Name(id=node.id + '_' + str(i), ctx=ast.Load()) for i in range(length)]
            return ast.copy_location(ast.Tuple(elts=elts, ctx=ast.Load()), node)
        elif node.id in self.npinstance_list.keys():
            npinstance_type = self.npinstance_list[node.id]
            shape = npinstance_type['shape']
            length = shape[0] * shape[1]
            dtype = npinstance_type['dtype']
            if dtype == 'complex128':
                elts = []
                for i in range(length):
                    elts.append(ast.Name(id=node.id + '_' + str(i) + '_real', ctx=ast.Load()))
                    elts.append(ast.Name(id=node.id + '_' + str(i) + '_imag', ctx=ast.Load()))
            else:
                elts = [ast.Name(id=node.id + '_' + str(i), ctx=ast.Load()) for i in range(length)]
            return ast.copy_location(ast.Tuple(elts=elts, ctx=ast.Load()), node)
        elif node.id in self.complex_list.keys():
            return ast.copy_location(ast.Tuple(elts=[ast.Name(id=node.id + '_real', ctx=ast.Load()), ast.Name(id=node.id + '_imag', ctx=ast.Load())], ctx=ast.Load()), node)
        return node
    def visit_Call(self, node: ast.Call) -> Any:
        args = []
        for arg in node.args:
            args.append(self.visit(arg))
        ret_args = []
        ret_args_non_complex = []
        for arg in args:
            if isinstance(arg, ast.Tuple):
                for elt in arg.elts:
                    ret_args.append(elt)
            else:
                ret_args.append(arg)
        for arg in ret_args:
            if isinstance(arg, Complex):
                ret_args_non_complex.extend([arg.real, arg.imag])
            else:
                ret_args_non_complex.append(arg)
        node.args = ret_args_non_complex
        self.generic_visit(node)
        return node
            
    
    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        ret_args = []
        ret_args_non_complex = []
        for arg in args:
            if arg in self.array_list.keys():
                ret_args.extend(self.flatten_list(arg))
            elif arg in self.npinstance_list.keys():
                ret_args.extend(self.flatten_array(arg))
            else:
                ret_args.append(arg)
        for arg in ret_args:
            if arg in self.complex_list.keys():
                ret_args_non_complex.extend([arg + '_real', arg + '_imag'])
            else:
                ret_args_non_complex.append(arg)
        node.args.args = [ast.arg(arg=arg, annotation=None) for arg in ret_args_non_complex]
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
            elif isinstance(arg, Complex):
                ret_args.extend([arg.real, arg.imag])
            else:
                ret_args.append(arg)
        return ast.copy_location(ast.Tuple(elts=ret_args, ctx=ast.Load()), node)
