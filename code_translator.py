# Standard Library
import ast
import logging
from _ast import Call, FunctionDef, List
from logging import getLogger
from typing import Any

# Third Party Library
import astor
from analyzer import process
from config import Config
from function_translator import FunctionTranslator
from last_translator import LastTranslator
from parse_complex import Complex, ComplexNumGenerator
from pure_executer import PureExecuter
from return_translator import ReturnTranslator
from type_alias import Number, VariableDict

from division_optimizer import DivisionOptimizer


class CodeTranslator(ast.NodeTransformer):
    def __init__(self, code: str, main_func: str, config: Config) -> None:
        logger = getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(
            "./numpy_to_polyphony/.log/code_translator.log", mode="w"
        )
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        self.logger = logger
        self.config = config
        self.current_func = ""
        try:
            self.npalias = "np"
            self.code = code
            self.tree = ast.parse(code)
            logger.debug("tree in ast.parse:\n%s", astor.dump_tree(self.tree))
            pure_executer = PureExecuter()
            self.tree = pure_executer.visit(self.tree)
            logger.debug("PureExecuter:\n%s", astor.dump_tree(self.tree))
            self.complex_parser = ComplexNumGenerator()
            self.complex_parser.visit(self.tree)
            (
                self.import_list,
                self.call_func_list,
                self.function_defs,
                self.return_var,
                self.array_list,
                self.float_list,
                self.complex_list,
                self.np_list,
                self.func_return,
                self.number_list,
            ) = process(self.tree, main_func)
            logger.debug("return_var in process:\n%s", self.return_var)
            logger.debug("array_list in process:\n%s", self.array_list)
            logger.debug("float_list in process:\n%s", self.float_list)
            logger.debug("complex_list in process:\n%s", self.complex_list)
            logger.debug("np_list in process:\n%s", self.np_list)
            logger.debug("func_return in process:\n%s", self.func_return)
            logger.debug("\n")
            const_propagater = ConstPropagater(self.number_list)
            self.tree = const_propagater.visit(self.tree)
            logger.debug("tree in ConstPropagater:\n%s", astor.dump_tree(self.tree))
            logger.debug("\n")
            func_translator = FunctionTranslator(
                self.array_list,
                self.np_list,
                self.float_list,
                self.complex_list,
                self.npalias,
            )
            func_translator.visit(self.tree)
            logger.debug("lib_list in FunctionTranslator:\n%s", func_translator.get_lib_list())
            logger.debug("shapes in FunctionTranslator:\n%s", func_translator.get_shapes())
            logger.debug("tree in FunctionTranslator:\n%s", astor.dump_tree(self.tree))
            logger.debug("\n")
            self.lib_list = func_translator.get_lib_list()
            self.shapes = func_translator.get_shapes()
        except Exception as e:
            logger.exception(e)
            raise e

    def process(self) -> None:
        try:
            self.visit(self.tree)
            self.logger.debug("tree in CodeTranslator:\n%s", astor.dump_tree(self.tree))
            self.logger.debug("\n")
            self.return_translator = ReturnTranslator(
                self.np_list,
                self.array_list,
                self.float_list,
                self.complex_list,
                self.return_var,
            )
            self.return_translator.visit(self.tree)
            self.logger.debug("tree in ReturnTranslator:\n%s", astor.dump_tree(self.tree))
            self.logger.debug("\n")
            if self.config.is_config() and self.config.has_key("fixed_point_style"):
                fixed_point_style = self.config.get_preprocess_config()["fixed_point_style"]
                precision = fixed_point_style["precision"]
            else:
                precision = 48
            self.division_optimizer = DivisionOptimizer(self.number_list)
            self.division_optimizer.visit(self.tree)
            self.logger.debug("tree in DivisionOptimizer:\n%s", astor.dump_tree(self.tree))
            self.last_translator = LastTranslator(
                self.array_list,
                self.float_list,
                self.complex_list,
                self.np_list,
                self.return_var,
                self.func_return,
                precision=precision,
            )
            self.last_translator.visit(self.tree)
            self.logger.debug("tree in LastTranslator:\n%s", astor.dump_tree(self.tree))
            self.logger.debug("\n")
        except Exception as e:
            self.logger.exception(e)
            raise e

    def get_call_func_list(self) -> list[str]:
        return self.call_func_list

    def get_import_list(self) -> list[str]:
        return self.import_list

    def get_function_defs(self) -> list[str]:
        return self.function_defs

    def get_np_list(self) -> VariableDict:
        return self.np_list

    def get_code(self) -> str:
        return self.code

    def get_array_list(self) -> VariableDict:
        return self.array_list

    def get_tree(self) -> ast.AST:
        return self.tree

    def get_func_return(self) -> VariableDict:
        return self.func_return

    def get_float_list(self) -> VariableDict:
        return self.float_list

    def get_complex_list(self) -> VariableDict:
        return self.complex_list

    def get_return_var(self) -> dict[str, str]:
        return self.return_var

    def get_lib_list(self) -> list[str]:
        return self.lib_list

    def get_shapes(self) -> list[tuple[int, ...]]:
        return self.shapes

    def get_np_alias(self) -> str:
        return self.npalias
    
    def get_number_list(self) -> dict[str, Number]:
        return self.number_list

    def flatten_list(self, list_name: str) -> list:
        list_type = self.array_list[list_name]
        shape = list_type["shape"]
        length = shape[0] * shape[1]
        list_names = []
        for i in range(length):
            list_names.append(list_name + "_" + str(i))
        return list_names

    def flatten_array(self, array_name: str) -> list:
        array_type = self.array_list[array_name]
        shape = array_type["shape"]
        length = shape[0] * shape[1]
        array_names = []
        for i in range(length):
            array_names.append(array_name + "_" + str(i))
        return array_names

    def visit_Call(self, node: Call) -> Any:
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

    def visit_List(self, node: List) -> Any:
        args = []
        for elt in node.elts:
            args.append(self.visit(elt))
        ret_args = []
        for arg in args:
            if isinstance(arg, ast.Tuple):
                for elt in arg.elts:
                    ret_args.append(elt)
            elif isinstance(arg, List):
                for elt in arg.elts:
                    ret_args.append(elt)
            else:
                ret_args.append(arg)
        return ast.copy_location(ast.List(elts=ret_args, ctx=ast.Load()), node)

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.current_func = node.name
        return self.generic_visit(node)


class ConstPropagater(ast.NodeTransformer):
    def __init__(self, number_list: dict[str, Number]):
        self.number_list = number_list
        self.current_func = ""

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.current_func = node.name
        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> Any:
        arg_name = self.current_func + "." + node.id
        if arg_name in self.number_list:
            return ast.copy_location(ast.Constant(n=self.number_list[arg_name]), node)
        else:
            return node
