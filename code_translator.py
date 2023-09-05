# Standard Library
import ast
import logging
from _ast import Call, FunctionDef, List
from logging import getLogger
from typing import Any

# Third Party Library
import astor
from analyzer import process
from function_translator import FunctionTranslator
from last_translator import LastTranslator
from parse_complex import ComplexNumGenerator
from return_translator import ReturnTranslator
from type_alias import VariableDict


class CodeTranslator(ast.NodeTransformer):
    def __init__(self, code: str) -> None:
        logger = getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(
            "./numpy_to_polyphony/.log/code_translator.log", mode="w"
        )
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        self.logger = logger
        self.current_func = ""
        try:
            self.npalias = "np"
            self.code = code
            self.tree = ast.parse(code)
            self.complex_parser = ComplexNumGenerator()
            self.complex_parser.visit(self.tree)
            (
                self.return_var,
                self.array_list,
                self.float_list,
                self.complex_list,
                self.np_list,
                self.func_return,
            ) = process(self.tree)
            logger.debug("return_var in process:\n%s", self.return_var)
            logger.debug("array_list in process:\n%s", self.array_list)
            logger.debug("float_list in process:\n%s", self.float_list)
            logger.debug("complex_list in process:\n%s", self.complex_list)
            logger.debug("np_list in process:\n%s", self.np_list)
            logger.debug("func_return in process:\n%s", self.func_return)
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
            self.last_translator = LastTranslator(
                self.array_list,
                self.float_list,
                self.complex_list,
                self.np_list,
                self.return_var,
                self.func_return,
            )
            self.last_translator.visit(self.tree)
            self.logger.debug("tree in LastTranslator:\n%s", astor.dump_tree(self.tree))
            self.logger.debug("\n")
        except Exception as e:
            self.logger.exception(e)
            raise e

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
        for arg in args:
            if isinstance(arg, ast.Tuple):
                for elt in arg.elts:
                    ret_args.append(elt)
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
            elif isinstance(arg, List):
                for elt in arg.elts:
                    ret_args.append(elt)
            else:
                ret_args.append(arg)
        return ast.copy_location(ast.List(elts=ret_args, ctx=ast.Load()), node)

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.current_func = node.name
        return self.generic_visit(node)
