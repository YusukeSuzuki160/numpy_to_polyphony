# Standard Library
import ast
import copy
import itertools
import logging
from _ast import (
    AST,
    Add,
    Assign,
    Attribute,
    BinOp,
    Call,
    FunctionDef,
    List,
    MatMult,
    Mult,
    Name,
    Return,
    Sub,
    Subscript,
    UnaryOp,
)
from logging import getLogger
from typing import Any, Tuple

import astor

# Third Party Library
from parse_complex import Complex
from type_alias import VariableDict


def process(
    tree: AST, main_func: str
) -> Tuple[VariableDict, VariableDict, VariableDict, VariableDict, VariableDict, VariableDict]:
    logger = getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler("./numpy_to_polyphony/.log/analyzer.log", mode="w")
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    try:
        logger.debug("tree in ast.parse:\n%s", astor.dump_tree(tree))
        logger.debug("\n")
        logger.debug("main_func: %s", main_func)
        immidiateassignanalyzer = ImmidiateAssignAnalyzer()
        immidiateassignanalyzer.visit(tree)
        logger.debug(
            "array_list in ImmidiateAssignAnalyzer:\n%s",
            immidiateassignanalyzer.array_list,
        )
        logger.debug(
            "float_list in ImmidiateAssignAnalyzer:\n%s",
            immidiateassignanalyzer.float_list,
        )
        logger.debug(
            "complex_list in ImmidiateAssignAnalyzer:\n%s",
            immidiateassignanalyzer.complex_list,
        )
        logger.debug("np_list in ImmidiateAssignAnalyzer:\n%s", immidiateassignanalyzer.np_list)
        logger.debug("\n")
        mainargnamelister = MainArgNameLister(main_func=main_func)
        mainargnamelister.visit(tree)
        logger.debug("arg_name_list in MainArgNameLister:\n%s", mainargnamelister.arg_name_list)
        logger.debug("\n")
        arg_name_list = mainargnamelister.arg_name_list
        maincallanalyzer = MainCallAnalyzer(
            arg_name_list,
            immidiateassignanalyzer.array_list,
            immidiateassignanalyzer.float_list,
            immidiateassignanalyzer.complex_list,
            immidiateassignanalyzer.np_list,
            main_func=main_func,
        )
        maincallanalyzer.visit(tree)
        array_list = maincallanalyzer.array_list
        float_list = maincallanalyzer.float_list
        complex_list = maincallanalyzer.complex_list
        np_list = maincallanalyzer.np_list
        logger.debug("array_list in MainCallAnalyzer:\n%s", array_list)
        logger.debug("float_list in MainCallAnalyzer:\n%s", float_list)
        logger.debug("complex_list in MainCallAnalyzer:\n%s", complex_list)
        logger.debug("np_list in MainCallAnalyzer:\n%s", np_list)
        logger.debug("\n")
        typeanalyzer = TypeAnalyzer(array_list, float_list, complex_list, np_list)
        typeanalyzer.visit(tree)
        logger.debug("np_list in TypeAnalyzer:\n%s", typeanalyzer.np_list)
        logger.debug("array_list in TypeAnalyzer:\n%s", typeanalyzer.array_list)
        logger.debug("float_list in TypeAnalyzer:\n%s", typeanalyzer.float_list)
        logger.debug("complex_list in TypeAnalyzer:\n%s", typeanalyzer.complex_list)
        logger.debug("\n")
        functionanalyzer = FunctionAnalyzer(
            array_list,
            typeanalyzer.float_list,
            typeanalyzer.complex_list,
            typeanalyzer.np_list,
        )
        functionanalyzer.visit(tree)
        logger.debug("func_return in FunctionAnalyzer:\n%s", functionanalyzer.func_return)
        logger.debug("np_list in FunctionAnalyzer:\n%s", functionanalyzer.np_list)
        logger.debug("array_list in FunctionAnalyzer:\n%s", functionanalyzer.array_list)
        logger.debug("float_list in FunctionAnalyzer:\n%s", functionanalyzer.float_list)
        logger.debug("complex_list in FunctionAnalyzer:\n%s", functionanalyzer.complex_list)
        logger.debug("\n")
        functioncallanalyzer = FunctionCallAnalyzer(
            functionanalyzer.array_list,
            functionanalyzer.float_list,
            functionanalyzer.complex_list,
            functionanalyzer.np_list,
            functionanalyzer.func_return,
        )
        functioncallanalyzer.visit(tree)
        logger.debug("array_list in FunctionCallAnalyzer:\n%s", functioncallanalyzer.array_list)
        logger.debug("float_list in FunctionCallAnalyzer:\n%s", functioncallanalyzer.float_list)
        logger.debug(
            "complex_list in FunctionCallAnalyzer:\n%s",
            functioncallanalyzer.complex_list,
        )
        logger.debug("np_list in FunctionCallAnalyzer:\n%s", functioncallanalyzer.np_list)
        logger.debug("func_return in FunctionCallAnalyzer:\n%s", functioncallanalyzer.func_return)
        logger.debug("\n")
        returnanalyzer = ReturnAnalyzer()
        returnanalyzer.visit(tree)
        logger.debug("return_var in ReturnAnalyzer:\n%s", returnanalyzer.return_var)
        logger.debug("\n")
    except Exception as e:
        logger.exception(e)
        raise e
    return (
        returnanalyzer.return_var,
        array_list,
        float_list,
        complex_list,
        functionanalyzer.np_list,
        functionanalyzer.func_return,
    )


def get_shape_from_list(list_node: List | ast.expr) -> list[int]:
    if isinstance(list_node, List):
        return list(itertools.chain([len(list_node.elts)], get_shape_from_list(list_node.elts[0])))
    else:
        return [1]


class ImmidiateAssignAnalyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.array_list: VariableDict = {}
        self.float_list: VariableDict = {}
        self.complex_list: VariableDict = {}
        self.np_list: VariableDict = {}
        self.current_func = ""

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.current_func = node.name
        self.generic_visit(node)

    def visit_Assign(self, node: Assign) -> Any:
        if isinstance(node.value, ast.Num):
            assert isinstance(node.targets[0], Name)  # TODO: support subscript
            arg_name = node.targets[0].id
            append_dict = {}
            func_name = self.current_func
            arg_name = func_name + "." + arg_name
            append_dict["scope"] = func_name
            if isinstance(node.value.n, float):
                type = "float64"
                append_dict["dtype"] = type
                self.float_list[arg_name] = append_dict

        elif isinstance(node.value, Complex):
            assert isinstance(node.targets[0], Name)  # TODO: support subscript
            arg_name = node.targets[0].id
            append_dict = {}
            func_name = self.current_func
            arg_name = func_name + "." + arg_name
            append_dict["scope"] = func_name
            append_dict["dtype"] = "complex128"
            self.complex_list[arg_name] = append_dict

        elif isinstance(node.value, Call):
            if (
                isinstance(node.value.func, Attribute)
                and isinstance(node.value.func.value, Name)
                and node.value.func.value.id == "np"
            ):
                if node.value.func.attr == "array":
                    if isinstance(node.value.args[0], List):
                        assert isinstance(node.targets[0], Name)
                        arg_name = node.targets[0].id
                        func_name = self.current_func
                        arg_name = func_name + "." + arg_name
                        append_dict = {}
                        append_dict["scope"] = func_name
                        append_dict["shape"] = get_shape_from_list(node.value.args[0])
                        element = node.value.args[0].elts[0]
                        shape = append_dict["shape"]
                        assert isinstance(shape, list)
                        while isinstance(element, List):
                            element = element.elts[0]
                        if isinstance(element, Complex):
                            dtype = "complex128"
                        else:
                            assert isinstance(element, ast.Num)
                            if isinstance(element.n, int):
                                dtype = "int64"
                            elif isinstance(element.n, float):
                                dtype = "float64"
                            elif isinstance(element.n, bool):
                                dtype = "bool"
                            else:
                                dtype = "object"
                        if node.value.keywords != []:
                            if node.value.keywords[0].arg == "dtype":
                                dtype = node.value.keywords[0].value.value.id
                        append_dict["dtype"] = dtype
                        self.np_list[arg_name] = append_dict
                    elif isinstance(node.value.args[0], Name):
                        assert isinstance(node.targets[0], Name)
                        id_name = node.targets[0].id
                        func_name = self.current_func
                        id_name = func_name + "." + id_name
                        arg_name = node.value.args[0].id
                        arg_name = func_name + "." + arg_name
                        assert arg_name in self.np_list or arg_name in self.array_list
                        if arg_name in self.np_list:
                            self.np_list[id_name] = copy.deepcopy(self.np_list[arg_name])
                            self.np_list[id_name]["scope"] = func_name
                        elif arg_name in self.array_list:
                            self.np_list[id_name] = copy.deepcopy(self.array_list[arg_name])
                            self.np_list[id_name]["scope"] = func_name
        elif isinstance(node.value, List):
            assert isinstance(node.targets[0], Name)
            arg_name = node.targets[0].id
            func_name = self.current_func
            arg_name = func_name + "." + arg_name
            append_dict = {}
            append_dict["scope"] = func_name
            append_dict["shape"] = get_shape_from_list(node.value)
            element = node.value.elts[0]
            shape = append_dict["shape"]
            assert isinstance(shape, list)
            while isinstance(element, List):
                element = element.elts[0]
            if isinstance(element, Complex):
                dtype = "complex128"
            else:
                assert isinstance(element, ast.Num)
                if isinstance(element.n, int):
                    dtype = "int64"
                elif isinstance(element.n, float):
                    dtype = "float64"
                elif isinstance(element.n, bool):
                    dtype = "bool"
                else:
                    dtype = "object"
            append_dict["dtype"] = dtype
            self.array_list[arg_name] = append_dict

        elif isinstance(node.value, BinOp):
            if isinstance(node.value.left, ast.Constant) or isinstance(
                node.value.right, ast.Constant
            ):
                if isinstance(node.value.left.value, float):
                    assert isinstance(node.targets[0], Name)
                    arg_name = node.targets[0].id
                    func_name = self.current_func
                    arg_name = func_name + "." + arg_name
                    append_dict = {}
                    append_dict["scope"] = func_name
                    append_dict["dtype"] = "float64"
                    self.float_list[arg_name] = append_dict
                elif isinstance(node.value.left.value, complex):
                    assert isinstance(node.targets[0], Name)
                    arg_name = node.targets[0].id
                    func_name = self.current_func
                    arg_name = func_name + "." + arg_name
                    append_dict = {}
                    append_dict["scope"] = func_name
                    append_dict["dtype"] = "complex128"
                    self.complex_list[arg_name] = append_dict
        elif isinstance(node.value, UnaryOp):
            if isinstance(node.value.operand, ast.Constant):
                if isinstance(node.value.operand.value, float):
                    assert isinstance(node.targets[0], Name)
                    arg_name = node.targets[0].id
                    func_name = self.current_func
                    arg_name = func_name + "." + arg_name
                    append_dict = {}
                    append_dict["scope"] = func_name
                    append_dict["dtype"] = "float64"
                    self.float_list[arg_name] = append_dict
                elif isinstance(node.value.operand.value, complex):
                    assert isinstance(node.targets[0], Name)
                    arg_name = node.targets[0].id
                    func_name = self.current_func
                    arg_name = func_name + "." + arg_name
                    append_dict = {}
                    append_dict["scope"] = func_name
                    append_dict["dtype"] = "complex128"
                    self.complex_list[arg_name] = append_dict
        self.generic_visit(node)


class MainArgNameLister(ast.NodeVisitor):
    def __init__(self, main_func: str) -> None:
        self.arg_name_list: dict[str, str] = {}
        self.main_func = main_func
        self.current_arg = 0

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        if node.name == self.main_func:
            for arg in node.args.args:
                arg_name = self.main_func + "_arg" + str(self.current_arg)
                self.arg_name_list[arg_name] = arg.arg
                self.current_arg += 1
        self.generic_visit(node)


class MainCallAnalyzer(ast.NodeVisitor):
    def __init__(
        self,
        arg_name_list: VariableDict,
        array_list: VariableDict,
        float_list: VariableDict,
        complex_list: VariableDict,
        np_list: VariableDict,
        main_func: str,
    ) -> None:
        self.array_list = array_list
        self.float_list = float_list
        self.complex_list = complex_list
        self.main_args = arg_name_list
        self.np_list = np_list
        self.main_func = main_func
        self.func_name = ""

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.func_name = node.name
        self.generic_visit(node)

    def visit_Call(self, node: Call) -> Any:
        if isinstance(node.func, Name) and node.func.id == self.main_func:
            i = 0
            for arg in node.args:
                if isinstance(arg, List):
                    arg_name = node.func.id + "_arg" + str(i)
                    append_dict = {}
                    func_name = node.func.id
                    append_dict["scope"] = func_name
                    shape = get_shape_from_list(arg)
                    if len(shape) == 1:
                        shape = [1] + shape
                    append_dict["shape"] = shape
                    element = arg.elts[0]
                    while isinstance(element, List):
                        element = element.elts[0]
                    if isinstance(element, Complex):
                        dtype = "complex128"
                    else:
                        assert isinstance(element, ast.Num)  # TODO: support subscript
                        if isinstance(element.n, int):
                            dtype = "int64"
                        elif isinstance(element.n, float):
                            dtype = "float64"
                        elif isinstance(element.n, bool):
                            dtype = "bool"
                        elif isinstance(element.n, complex):
                            dtype = "complex128"
                        else:
                            dtype = "object"
                    append_dict["dtype"] = dtype
                    arg_name = func_name + "." + self.main_args[arg_name]
                    self.array_list[arg_name] = append_dict
                    if dtype == "float64":
                        length = shape[0] * shape[1]
                        for j in range(length):
                            self.float_list[arg_name + "_" + str(j)] = append_dict
                    elif dtype == "complex128":
                        length = shape[0] * shape[1]
                        for j in range(length):
                            self.complex_list[arg_name + "_" + str(j)] = append_dict
                    i += 1
                elif isinstance(arg, ast.Num):
                    if isinstance(arg.n, float):
                        append_dict = {}
                        func_name = node.func.id
                        append_dict["scope"] = func_name
                        append_dict["dtype"] = "float64"
                        arg_name = (
                            func_name + "." + self.main_args[self.main_func + "_arg" + str(i)]
                        )
                        self.float_list[arg_name] = append_dict
                    i += 1
                elif isinstance(arg, Complex):
                    append_dict = {}
                    func_name = node.func.id
                    append_dict["scope"] = func_name
                    append_dict["dtype"] = "complex128"
                    arg_name = func_name + "." + self.main_args[self.main_func + "_arg" + str(i)]
                    self.complex_list[arg_name] = append_dict
                    i += 1
                elif isinstance(arg, Name):
                    func_name = node.func.id
                    current_func = self.func_name
                    arg_name = func_name + "." + self.main_args[self.main_func + "_arg" + str(i)]
                    id_name = current_func + "." + arg.id
                    if id_name in self.array_list:
                        self.array_list[arg_name] = copy.deepcopy(self.array_list[id_name])
                        self.array_list[arg_name]["scope"] = func_name
                    elif id_name in self.np_list:
                        self.np_list[arg_name] = copy.deepcopy(self.np_list[id_name])
                        self.np_list[arg_name]["scope"] = func_name
                    elif id_name in self.float_list:
                        self.float_list[arg_name] = copy.deepcopy(self.float_list[id_name])
                        self.float_list[arg_name]["scope"] = func_name
                    elif id_name in self.complex_list:
                        self.complex_list[arg_name] = copy.deepcopy(self.complex_list[id_name])
                        self.complex_list[arg_name]["scope"] = func_name
                    i += 1
                elif isinstance(arg, UnaryOp):
                    if isinstance(arg.operand, ast.Constant):
                        num = arg.operand.value
                        if isinstance(num, float):
                            append_dict = {}
                            func_name = node.func.id
                            append_dict["scope"] = func_name
                            append_dict["dtype"] = "float64"
                            arg_name = (
                                func_name + "." + self.main_args[self.main_func + "_arg" + str(i)]
                            )
                            self.float_list[arg_name] = append_dict
                            i += 1
        self.generic_visit(node)

    def visit_Assign(self, node: Assign) -> Any:
        if isinstance(node.value, List):
            assert isinstance(node.targets[0], Name)  # TODO: support subscript
            arg_name = node.targets[0].id
            append_dict = {}
            func_name = self.func_name
            append_dict["scope"] = func_name
            shape = get_shape_from_list(node.value)
            arg_name = func_name + "." + arg_name
            if len(shape) == 1:
                shape = [1] + shape
            append_dict["shape"] = shape
            element = node.value.elts[0]
            while isinstance(element, List):
                element = element.elts[0]
            if isinstance(element, Complex):
                dtype = "complex128"
            else:
                assert isinstance(element, ast.Num)
                if isinstance(element.n, int):
                    dtype = "int64"
                elif isinstance(element.n, float):
                    dtype = "float64"
                elif isinstance(element.n, bool):
                    dtype = "bool"
                elif isinstance(element.n, complex):
                    dtype = "complex128"
                else:
                    dtype = "object"
            append_dict["dtype"] = dtype
            self.array_list[arg_name] = append_dict
            if dtype == "float64":
                length = shape[0] * shape[1]
                for j in range(length):
                    self.float_list[arg_name + "_" + str(j)] = append_dict
            elif dtype == "complex128":
                length = shape[0] * shape[1]
                for j in range(length):
                    self.complex_list[arg_name + "_" + str(j)] = append_dict
        self.generic_visit(node)


class TypeAnalyzer(ast.NodeVisitor):
    def __init__(
        self,
        arg_name_list: VariableDict,
        float_list: VariableDict,
        complex_list: VariableDict,
        np_list: VariableDict,
    ) -> None:
        self.array_list = arg_name_list
        self.float_list = float_list
        self.complex_list = complex_list
        self.np_list = np_list
        self.current_func = ""

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.current_func = node.name
        self.generic_visit(node)

    def visit_Assign(self, node: Assign) -> Any:
        if isinstance(node.value, Call):
            if (
                isinstance(node.value.func, Attribute)
                and isinstance(node.value.func.value, Name)
                and node.value.func.value.id == "np"
            ):
                if node.value.func.attr == "array":
                    if isinstance(node.value.args[0], List):
                        assert isinstance(node.targets[0], Name)  # TODO: support subscript
                        arg_name = node.targets[0].id
                        append_dict = {}
                        func_name = self.current_func
                        append_dict["scope"] = func_name
                        append_dict["shape"] = get_shape_from_list(node.value.args[0])
                        element = node.value.args[0].elts[0]
                        arg_name = func_name + "." + arg_name
                        shape = append_dict["shape"]
                        assert isinstance(shape, list)
                        while isinstance(element, List):
                            element = element.elts[0]
                        if isinstance(element, Complex):
                            dtype = "complex128"
                        else:
                            assert isinstance(element, ast.Num)
                            if isinstance(element.n, int):
                                dtype = "int64"
                            elif isinstance(element.n, float):
                                dtype = "float64"
                            elif isinstance(element.n, bool):
                                dtype = "bool"
                            elif isinstance(element.n, complex):
                                dtype = "complex128"
                            else:
                                dtype = "object"
                        if node.value.keywords != []:
                            if node.value.keywords[0].arg == "dtype":
                                dtype = node.value.keywords[0].value.value.id
                        append_dict["dtype"] = dtype
                        self.np_list[arg_name] = append_dict
                        if dtype == "float64":
                            length = shape[0] * shape[1]
                            for j in range(length):
                                self.float_list[arg_name + "_" + str(j)] = append_dict
                        elif dtype == "complex128":
                            length = shape[0] * shape[1]
                            for j in range(length):
                                self.complex_list[arg_name + "_" + str(j)] = append_dict
                    if isinstance(node.value.args[0], Name):
                        assert isinstance(node.targets[0], Name)  # TODO: support subscript
                        arg_name = node.targets[0].id
                        func_name = self.current_func
                        arg_name = func_name + "." + arg_name
                        id_name = func_name + "." + node.value.args[0].id
                        append_dict = {}
                        append_dict = self.array_list[id_name]
                        append_dict["scope"] = func_name
                        dtype = append_dict["dtype"]
                        if node.value.keywords != []:
                            if node.value.keywords[0].arg == "dtype":
                                dtype = node.value.keywords[0].value.attr
                                append_dict["dtype"] = dtype
                        self.np_list[arg_name] = append_dict
                        shape = append_dict["shape"]
                        assert isinstance(shape, list)
                        length = shape[0] * shape[1]
                        if dtype == "float64":
                            for j in range(length):
                                self.float_list[arg_name + "_" + str(j)] = append_dict
                        elif dtype == "complex128":
                            for j in range(length):
                                self.complex_list[arg_name + "_" + str(j)] = append_dict

                elif node.value.func.attr == "cov":
                    if isinstance(node.value.args[0], Name):
                        assert isinstance(node.targets[0], Name)
                        arg_name = node.targets[0].id
                        func_name = self.current_func
                        arg_name = func_name + "." + arg_name
                        id_name = func_name + "." + node.value.args[0].id
                        append_dict = copy.deepcopy(self.np_list[id_name])
                        append_dict["scope"] = func_name
                        rowvar = [kw for kw in node.value.keywords if kw.arg == "rowvar"]
                        shape = append_dict["shape"]
                        if rowvar != []:
                            rowvar = rowvar[0].value.value
                            if rowvar == True:
                                shape = (shape[0], shape[0])
                            else:
                                shape = (shape[1], shape[1])
                        else:
                            shape = (shape[1], shape[1])
                        append_dict["shape"] = shape
                        self.np_list[arg_name] = append_dict

                elif node.value.func.attr == "argsort":
                    if isinstance(node.value.args[0], Name):
                        assert isinstance(node.targets[0], Name)
                        arg_name = node.targets[0].id
                        func_name = self.current_func
                        arg_name = func_name + "." + arg_name
                        id_name = func_name + "." + node.value.args[0].id
                        append_dict = copy.deepcopy(self.np_list[id_name])
                        append_dict["scope"] = func_name
                        self.np_list[arg_name] = append_dict

                elif node.value.func.attr == "mean":
                    if isinstance(node.value.args[0], Name):
                        assert isinstance(node.targets[0], Name)
                        axis = [kw for kw in node.value.keywords if kw.arg == "axis"]
                        if axis != []:
                            axis = axis[0].value.n
                            if axis == 0:
                                arg_name = node.targets[0].id
                                func_name = self.current_func
                                arg_name = func_name + "." + arg_name
                                id_name = func_name + "." + node.value.args[0].id
                                append_dict = copy.deepcopy(self.np_list[id_name])
                                append_dict["scope"] = func_name
                                shape = append_dict["shape"]
                                shape = [1, shape[1]]
                                append_dict["shape"] = shape
                                self.np_list[arg_name] = append_dict
                            elif axis == 1:
                                arg_name = node.targets[0].id
                                func_name = self.current_func
                                arg_name = func_name + "." + arg_name
                                id_name = func_name + "." + node.value.args[0].id
                                append_dict = copy.deepcopy(self.np_list[id_name])
                                append_dict["scope"] = func_name
                                shape = append_dict["shape"]
                                shape = [shape[0], 1]
                                append_dict["shape"] = shape
                                self.np_list[arg_name] = append_dict

                elif node.value.func.attr == "fft":
                    if isinstance(node.value.func.value.value, ast.Name):
                        if node.value.func.value.value.id == "np":
                            if isinstance(node.value.args[0], ast.Name):
                                assert isinstance(node.targets[0], Name)  # TODO: support subscript
                                arg_name = node.targets[0].id
                                func_name = self.current_func
                                arg_name = func_name + "." + arg_name
                                append_dict = self.np_list[arg_name]
                                append_dict["scope"] = func_name
                                append_dict["dtype"] = "complex128"
                                shape = append_dict["shape"]
                                length = shape[0] * shape[1]
                                for j in range(length):
                                    self.complex_list[arg_name + "_" + str(j)] = append_dict
                                self.np_list[arg_name] = append_dict
            elif (
                isinstance(node.value.func, Attribute)
                and isinstance(node.value.func.value, Attribute)
                and isinstance(node.value.func.value.value, ast.Name)
                and node.value.func.value.value.id == "np"
            ):
                if node.value.func.value.attr == "linalg":
                    if node.value.func.attr == "qr":
                        assert isinstance(node.targets[0], ast.Tuple)
                        arg_Q = node.targets[0].elts[0].id
                        arg_R = node.targets[0].elts[1].id
                        func_name = self.current_func
                        arg_Q = func_name + "." + arg_Q
                        arg_R = func_name + "." + arg_R
                        id_name = func_name + "." + node.value.args[0].id
                        append_dict = copy.deepcopy(self.np_list[id_name])
                        append_dict["scope"] = func_name
                        self.np_list[arg_Q] = append_dict
                        self.np_list[arg_R] = append_dict
                    elif node.value.func.attr == "eigh":
                        assert isinstance(node.targets[0], ast.Tuple)
                        arg_W = node.targets[0].elts[0].id
                        arg_V = node.targets[0].elts[1].id
                        func_name = self.current_func
                        arg_W = func_name + "." + arg_W
                        arg_V = func_name + "." + arg_V
                        id_name = func_name + "." + node.value.args[0].id
                        append_dict_W = copy.deepcopy(self.np_list[id_name])
                        append_dict_W["scope"] = func_name
                        shape_W = append_dict_W["shape"]
                        shape_W = [shape_W[0], 1]
                        append_dict_V = copy.deepcopy(self.np_list[id_name])
                        append_dict_V["scope"] = func_name
                        self.np_list[arg_W] = append_dict_W
                        self.np_list[arg_V] = append_dict_V
        elif isinstance(node.value, ast.Num):
            assert isinstance(node.targets[0], Name)  # TODO: support subscript
            arg_name = node.targets[0].id
            append_dict = {}
            func_name = self.current_func
            arg_name = func_name + "." + arg_name
            append_dict["scope"] = func_name
            if isinstance(node.value.n, float):
                type = "float64"
                append_dict["dtype"] = type
                self.float_list[arg_name] = append_dict

        elif isinstance(node.value, Complex):
            assert isinstance(node.targets[0], Name)  # TODO: support subscript
            arg_name = node.targets[0].id
            append_dict = {}
            func_name = self.current_func
            arg_name = func_name + "." + arg_name
            append_dict["scope"] = func_name
            append_dict["dtype"] = "complex128"
            self.complex_list[arg_name] = append_dict

        elif isinstance(node.value, Name):
            assert isinstance(node.targets[0], Name)  # TODO: support subscript
            func_name = self.current_func
            arg_name = func_name + "." + node.targets[0].id
            id_name = func_name + "." + node.value.id
            if id_name in self.np_list:
                self.np_list[arg_name] = self.np_list[id_name]
                self.np_list[arg_name]["scope"] = func_name
            elif id_name in self.float_list:
                self.float_list[arg_name] = self.float_list[id_name]
                self.float_list[arg_name]["scope"] = func_name
            elif id_name in self.complex_list:
                self.complex_list[arg_name] = self.complex_list[id_name]
                self.complex_list[arg_name]["scope"] = func_name
        elif isinstance(node.value, BinOp):
            self.visit(node.value)
            assert isinstance(node.targets[0], Name)  # TODO: support subscript
            assert isinstance(node.value.left, Name)  # TODO: support subscript
            assert isinstance(node.value.right, Name)  # TODO: support subscript
            func_name = self.current_func
            arg_name = func_name + "." + node.targets[0].id
            left_name = func_name + "." + node.value.left.id
            right_name = func_name + "." + node.value.right.id
            if left_name not in self.np_list.keys():
                if left_name in self.float_list.keys():
                    self.float_list[arg_name] = self.float_list[left_name]
                    self.float_list[arg_name]["scope"] = func_name
                    self.generic_visit(node)
                    return
                elif left_name in self.complex_list.keys():
                    self.complex_list[arg_name] = self.complex_list[left_name]
                    self.complex_list[arg_name]["scope"] = func_name
                    self.generic_visit(node)
                    return
            left_type = self.np_list[left_name]["dtype"]
            right_type = self.np_list[right_name]["dtype"]
            assert left_type == right_type
            left_shape = self.np_list[left_name]["shape"]
            right_shape = self.np_list[right_name]["shape"]
            dtype = left_type
            append_dict = {}
            append_dict["scope"] = func_name
            if (
                isinstance(node.value.op, Add)
                or isinstance(node.value.op, Sub)
                or isinstance(node.value.op, Mult)
            ):
                shape = left_shape
                append_dict["shape"] = shape
            elif isinstance(node.value.op, MatMult):
                shape = [left_shape[0], right_shape[1]]
                assert left_shape[1] == right_shape[0]
                append_dict["shape"] = shape
            append_dict["dtype"] = dtype
            self.np_list[arg_name] = append_dict
        elif isinstance(node.value, UnaryOp):
            self.visit(node.value)
            if isinstance(node.value.operand, ast.Constant):
                return
            assert isinstance(node.targets[0], Name)  # TODO: support subscript
            assert isinstance(node.value.operand, Name)  # TODO: support subscript
            func_name = self.current_func
            arg_name = func_name + "." + node.targets[0].id
            id_name = func_name + "." + node.value.operand.id
            dtype = self.np_list[id_name]["dtype"]
            append_dict = {}
            append_dict["scope"] = func_name
            append_dict["dtype"] = dtype
            append_dict["shape"] = self.np_list[id_name]["shape"]
            self.np_list[arg_name] = append_dict
        elif isinstance(node.value, Subscript):
            self.visit(node.value)
            assert isinstance(node.targets[0], Name)  # TODO: support subscript
            assert isinstance(node.value.value, Name)  # TODO: support subscript
            if isinstance(node.value.slice, ast.Index):
                func_name = self.current_func
                arg_name = func_name + "." + node.targets[0].id
                id_name = func_name + "." + node.value.value.id
                dtype = self.np_list[id_name]["dtype"]
                append_dict = {}
                append_dict["scope"] = func_name
                append_dict["dtype"] = dtype
                append_dict["shape"] = self.np_list[id_name]["shape"][1:]
                self.np_list[arg_name] = append_dict
            elif isinstance(node.value.slice, ast.Slice):
                pass  # TODO: support slice
            elif isinstance(node.value.slice, ast.Name):
                func_name = self.current_func
                arg_name = func_name + "." + node.targets[0].id
                id_name = func_name + "." + node.value.slice.id
                dtype = self.np_list[id_name]["dtype"]
                append_dict = {}
                append_dict["scope"] = func_name
                append_dict["dtype"] = dtype
                append_dict["shape"] = self.np_list[id_name]["shape"]
                self.np_list[arg_name] = append_dict
            elif isinstance(node.value.slice, ast.Tuple):
                left = node.value.slice.elts[0]
                right = node.value.slice.elts[1]
                func_name = self.current_func
                arg_name = func_name + "." + node.targets[0].id
                id_name = func_name + "." + node.value.value.id
                dtype = self.np_list[id_name]["dtype"]
                append_dict = {}
                append_dict["scope"] = func_name
                append_dict["dtype"] = dtype
                shape = self.np_list[id_name]["shape"]
                if isinstance(left, ast.Num):
                    left = left.n
                elif isinstance(left, ast.Name):
                    left = self.np_list[func_name + "." + left.id]["shape"]
                elif isinstance(left, ast.Slice):
                    if left.lower is None:
                        lower = 0
                    else:
                        if isinstance(left.lower, ast.Num):
                            lower = left.lower.n
                        elif isinstance(left.lower, ast.UnaryOp):
                            lower = shape[0] - left.lower.operand.n
                    if left.upper is None:
                        upper = shape[0]
                    else:
                        upper = left.upper.n
                    if left.step is None:
                        step = 1
                    else:
                        step = left.step.n
                    left = (upper - lower) // step
                if isinstance(right, ast.Num):
                    right = right.n
                elif isinstance(right, ast.Name):
                    right = self.np_list[func_name + "." + right.id]["shape"]
                elif isinstance(right, ast.Slice):
                    if right.lower is None:
                        lower = 0
                    else:
                        if isinstance(right.lower, ast.Num):
                            lower = right.lower.n
                        elif isinstance(right.lower, ast.UnaryOp):
                            lower = shape[0] - right.lower.operand.n
                    if right.upper is None:
                        upper = shape[0]
                    else:
                        upper = right.upper.n
                    if right.step is None:
                        step = 1
                    else:
                        step = right.step.n
                    right = (upper - lower) // step
                if not isinstance(left, list):
                    left = [left]
                if not isinstance(right, list):
                    right = [right]
                append_dict["shape"] = list(itertools.chain(left, right))
                self.np_list[arg_name] = append_dict
        self.generic_visit(node)


class FunctionAnalyzer(ast.NodeVisitor):
    def __init__(
        self,
        array_list: VariableDict,
        float_list: VariableDict,
        complex_list: VariableDict,
        np_list: VariableDict,
    ) -> None:
        self.array_list = array_list
        self.float_list = float_list
        self.complex_list = complex_list
        self.np_list = np_list
        self.func_return: VariableDict = {}

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        if isinstance(node.body[-1], Return):
            if isinstance(node.body[-1].value, Name):
                func_name = node.name
                return_id = func_name + "." + node.body[-1].value.id
                if return_id in self.np_list:
                    self.func_return[func_name] = self.np_list[return_id]
                elif return_id in self.float_list:
                    self.func_return[func_name] = self.float_list[return_id]
                elif return_id in self.complex_list:
                    self.func_return[func_name] = self.complex_list[return_id]
                elif return_id in self.array_list:
                    self.func_return[func_name] = self.array_list[return_id]
            elif isinstance(node.body[-1].value, ast.Tuple):
                func_name = node.name
                for elt in node.body[-1].value.elts:
                    assert isinstance(elt, Name)
                    return_id = func_name + "." + elt.id
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
    def __init__(
        self,
        array_list: VariableDict,
        float_list: VariableDict,
        complex_list: VariableDict,
        np_list: VariableDict,
        func_return: VariableDict,
    ) -> None:
        self.array_list = array_list
        self.float_list = float_list
        self.complex_list = complex_list
        self.np_list = np_list
        self.func_return = func_return
        self.current_func = ""

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.current_func = node.name
        self.generic_visit(node)

    def visit_Assign(self, node: Assign) -> Any:
        if isinstance(node.value, Call):
            if isinstance(node.value.func, Name):
                if node.value.func.id in self.func_return.keys():
                    if isinstance(node.targets[0], Name):
                        dist_name = node.targets[0].id
                        src_type = self.func_return[node.value.func.id]
                        func_name = self.current_func
                        dist_name = func_name + "." + dist_name
                        if src_type.get("shape") is not None:
                            self.np_list[dist_name] = src_type
                            self.np_list[dist_name]["scope"] = func_name
                        else:
                            if "fixed" in src_type.get("dtype"):
                                self.float_list[dist_name] = src_type
                                self.float_list[dist_name]["scope"] = func_name
                            elif "complex" in src_type.get("dtype"):
                                self.complex_list[dist_name] = src_type
                                self.complex_list[dist_name]["scope"] = func_name
                    elif isinstance(node.targets[0], ast.Tuple):
                        for elt in node.targets[0].elts:
                            if isinstance(elt, Name):
                                dist_name = elt.id
                                src_type = self.func_return[node.value.func.id]
                                func_name = self.current_func
                                dist_name = func_name + "." + dist_name
                                if src_type.get("shape") is not None:
                                    self.np_list[dist_name] = src_type
                                    self.np_list[dist_name]["scope"] = func_name
                                else:
                                    if "fixed" in src_type.get("dtype"):
                                        self.float_list[dist_name] = src_type
                                        self.float_list[dist_name]["scope"] = func_name
                                    elif "complex" in src_type.get("dtype"):
                                        self.complex_list[dist_name] = src_type
                                        self.complex_list[dist_name]["scope"] = func_name

        self.generic_visit(node)


class ReturnAnalyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.return_var: dict[str, list[str]] = {}
        self.function_stack: list[str] = []

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    def visit_Return(self, node: Return) -> Any:
        if isinstance(node.value, Name):
            func_name = self.function_stack[-1]
            id_name = node.value.id
            self.return_var[func_name] = [id_name]
        elif isinstance(node.value, ast.Tuple):
            func_name = self.function_stack[-1]
            self.return_var[func_name] = []
            for elt in node.value.elts:
                assert isinstance(elt, Name)
                id_name = elt.id
                self.return_var[func_name].append(id_name)
        self.generic_visit(node)
