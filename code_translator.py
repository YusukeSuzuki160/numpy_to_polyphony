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
        print(self.function_call_analyzer.complex_list)
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

    def visit_Call(self, node: ast.Call) -> Any:
        args = []
        for arg in node.args:
            args.append(self.visit(arg))
        ret_args = []
        for arg in args:
            if isinstance(arg, ast.Tuple):
                for elt in arg.elts:
                    ret_args.append(elt)
            elif isinstance(arg, Complex):
                ret_args.extend([arg.real, arg.imag])
            else:
                ret_args.append(arg)
        node.args = ret_args
        self.generic_visit(node)
        return node
    
        
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
