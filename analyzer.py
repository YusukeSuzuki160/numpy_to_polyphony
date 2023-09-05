# Standard Library
import ast
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

# Third Party Library
from parse_complex import Complex
from type_alias import VariableDict


def process(
    tree: AST,
) -> Tuple[VariableDict, VariableDict, VariableDict, VariableDict, VariableDict, VariableDict]:
    logger = getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler("./numpy_to_polyphony/.log/analyzer.log", mode="w")
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    try:
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
        logger.debug("\n")
        mainargnamelister = MainArgNameLister()
        mainargnamelister.visit(tree)
        logger.debug("arg_name_list in MainArgNameLister:\n%s", mainargnamelister.arg_name_list)
        logger.debug("\n")
        arg_name_list = mainargnamelister.arg_name_list
        maincallanalyzer = MainCallAnalyzer(
            arg_name_list,
            immidiateassignanalyzer.array_list,
            immidiateassignanalyzer.float_list,
            immidiateassignanalyzer.complex_list,
        )
        maincallanalyzer.visit(tree)
        array_list = maincallanalyzer.array_list
        float_list = maincallanalyzer.float_list
        complex_list = maincallanalyzer.complex_list
        logger.debug("array_list in MainCallAnalyzer:\n%s", array_list)
        logger.debug("float_list in MainCallAnalyzer:\n%s", float_list)
        logger.debug("complex_list in MainCallAnalyzer:\n%s", complex_list)
        logger.debug("\n")
        typeanalyzer = TypeAnalyzer(array_list, float_list, complex_list)
        typeanalyzer.visit(tree)
        logger.debug("npinstance_list in TypeAnalyzer:\n%s", typeanalyzer.npinstance_list)
        logger.debug("array_list in TypeAnalyzer:\n%s", typeanalyzer.array_list)
        logger.debug("float_list in TypeAnalyzer:\n%s", typeanalyzer.float_list)
        logger.debug("complex_list in TypeAnalyzer:\n%s", typeanalyzer.complex_list)
        logger.debug("\n")
        functionanalyzer = FunctionAnalyzer(
            array_list,
            typeanalyzer.float_list,
            typeanalyzer.complex_list,
            typeanalyzer.npinstance_list,
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
        return [len(list_node.elts)] + get_shape_from_list(list_node.elts[0])
    else:
        return []


class ImmidiateAssignAnalyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.array_list: VariableDict = {}
        self.float_list: VariableDict = {}
        self.complex_list: VariableDict = {}
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

        elif isinstance(node.value, BinOp):
            pass
        elif isinstance(node.value, UnaryOp):
            pass
        self.generic_visit(node)


class MainArgNameLister(ast.NodeVisitor):
    def __init__(self) -> None:
        self.arg_name_list: dict[str, str] = {}
        self.current_arg = 0

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        if node.name == "main":
            for arg in node.args.args:
                arg_name = "main_arg" + str(self.current_arg)
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
    ) -> None:
        self.array_list = array_list
        self.float_list = float_list
        self.complex_list = complex_list
        self.main_args = arg_name_list
        self.func_name = ""

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.func_name = node.name
        self.generic_visit(node)

    def visit_Call(self, node: Call) -> Any:
        if isinstance(node.func, Name) and node.func.id == "main":
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
                        arg_name = func_name + "." + self.main_args["main_arg" + str(i)]
                        self.float_list[arg_name] = append_dict
                    i += 1
                elif isinstance(arg, Complex):
                    append_dict = {}
                    func_name = node.func.id
                    append_dict["scope"] = func_name
                    append_dict["dtype"] = "complex128"
                    arg_name = func_name + "." + self.main_args["main_arg" + str(i)]
                    self.complex_list[arg_name] = append_dict
                    i += 1
                elif isinstance(arg, Name):
                    func_name = node.func.id
                    current_func = self.func_name
                    arg_name = func_name + "." + self.main_args["main_arg" + str(i)]
                    id_name = current_func + "." + arg.id
                    if id_name in self.array_list:
                        self.array_list[arg_name] = self.array_list[id_name]
                        self.array_list[arg_name]["scope"] = func_name
                    elif id_name in self.float_list:
                        self.float_list[arg_name] = self.float_list[id_name]
                        self.float_list[arg_name]["scope"] = func_name
                    elif id_name in self.complex_list:
                        self.complex_list[arg_name] = self.complex_list[id_name]
                        self.complex_list[arg_name]["scope"] = func_name
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
                    self.float_list[self.main_args[arg_name] + "_" + str(j)] = append_dict
            elif dtype == "complex128":
                length = shape[0] * shape[1]
                for j in range(length):
                    self.complex_list[self.main_args[arg_name] + "_" + str(j)] = append_dict
        self.generic_visit(node)


class TypeAnalyzer(ast.NodeVisitor):
    def __init__(
        self, arg_name_list: VariableDict, float_list: VariableDict, complex_list: VariableDict
    ) -> None:
        self.array_list = arg_name_list
        self.float_list = float_list
        self.complex_list = complex_list
        self.npinstance_list: VariableDict = {}
        self.current_func = ""

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.current_func = node.name
        self.generic_visit(node)

    def visit_Assign(self, node: Assign) -> Any:
        if isinstance(node.value, Call):
            if isinstance(node.value.func, Attribute):
                if node.value.func.attr == "array":
                    if isinstance(node.value.func.value, Name):
                        if node.value.func.value.id == "np":
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
                                self.npinstance_list[arg_name] = append_dict
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
                                func_name = self.current_func
                                append_dict["scope"] = func_name
                                dtype = append_dict["dtype"]
                                if node.value.keywords != []:
                                    if node.value.keywords[0].arg == "dtype":
                                        dtype = node.value.keywords[0].value.attr
                                        append_dict["dtype"] = dtype
                                self.npinstance_list[arg_name] = append_dict
                                shape = append_dict["shape"]
                                assert isinstance(shape, list)
                                length = shape[0] * shape[1]
                                for j in range(length):
                                    self.complex_list[arg_name + "_" + str(j)] = append_dict
                elif node.value.func.attr == "fft":
                    if isinstance(node.value.func.value.value, ast.Name):
                        if node.value.func.value.value.id == "np":
                            if isinstance(node.value.args[0], ast.Name):
                                assert isinstance(node.targets[0], Name)  # TODO: support subscript
                                arg_name = node.targets[0].id
                                func_name = self.current_func
                                arg_name = func_name + "." + arg_name
                                append_dict = self.npinstance_list[arg_name]
                                append_dict["scope"] = func_name
                                append_dict["dtype"] = "complex128"
                                shape = append_dict["shape"]
                                length = shape[0] * shape[1]
                                for j in range(length):
                                    self.complex_list[arg_name + "_" + str(j)] = append_dict
                                self.npinstance_list[arg_name] = append_dict
                # elif node.value.func.attr == 'append':
                # if isinstance(node.value.func.value.value, ast.Name):
                # if node.value.func.value.value.id == 'np':
                # if isinstance(node.value.args[0], ast.Name):
                # arg_name = node.targets[0].id
                # append_dict = {}
                # append_dict = self.npinstance_list[node.value.args[0].id]
                # shape = append_dict['shape']
                # append_dict['shape'] = (1, shape[0] * shape[1] + 1)
                # self.npinstance_list[arg_name] = append_dict
                # shape = append_dict['shape']
                # length = shape[0] * shape[1]
                # for j in range(length):
                # self.complex_list[arg_name + '_' + str(j)] = 'complex128'

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
            if id_name in self.npinstance_list:
                self.npinstance_list[arg_name] = self.npinstance_list[id_name]
                self.npinstance_list[arg_name]["scope"] = func_name
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
            if left_name not in self.npinstance_list.keys():
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
            left_type = self.npinstance_list[left_name]["dtype"]
            right_type = self.npinstance_list[right_name]["dtype"]
            assert left_type == right_type
            left_shape = self.npinstance_list[left_name]["shape"]
            right_shape = self.npinstance_list[right_name]["shape"]
            dtype = left_type
            append_dict = {}
            append_dict["scope"] = func_name
            if (
                isinstance(node.value.op, Add)
                or isinstance(node.value.op, Sub)
                or isinstance(node.value.op, Mult)
            ):
                shape = left_shape
                assert shape == right_shape  # TODO: broadcast
                append_dict["shape"] = shape
            elif isinstance(node.value.op, MatMult):
                shape = [left_shape[0], right_shape[1]]
                assert left_shape[1] == right_shape[0]
                append_dict["shape"] = shape
            append_dict["dtype"] = dtype
            self.npinstance_list[arg_name] = append_dict
        elif isinstance(node.value, UnaryOp):
            self.visit(node.value)
            assert isinstance(node.targets[0], Name)  # TODO: support subscript
            assert isinstance(node.value.operand, Name)  # TODO: support subscript
            func_name = self.current_func
            arg_name = func_name + "." + node.targets[0].id
            id_name = func_name + "." + node.value.operand.id
            dtype = self.npinstance_list[id_name]["dtype"]
            append_dict = {}
            append_dict["scope"] = func_name
            append_dict["dtype"] = dtype
            append_dict["shape"] = self.npinstance_list[id_name]["shape"]
            self.npinstance_list[arg_name] = append_dict
        elif isinstance(node.value, Subscript):
            self.visit(node.value)
            assert isinstance(node.targets[0], Name)  # TODO: support subscript
            assert isinstance(node.value.value, Name)  # TODO: support subscript
            func_name = self.current_func
            arg_name = func_name + "." + node.targets[0].id
            id_name = func_name + "." + node.value.value.id
            dtype = self.npinstance_list[id_name]["dtype"]
            append_dict = {}
            append_dict["scope"] = func_name
            append_dict["dtype"] = dtype
            append_dict["shape"] = self.npinstance_list[id_name]["shape"][1:]
            self.npinstance_list[arg_name] = append_dict
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
            assert isinstance(node.body[-1].value, Name)
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
                    assert isinstance(node.targets[0], Name)  # TODO: support subscript
                    dist_name = node.targets[0].id
                    src_type = self.func_return[node.value.func.id]
                    func_name = self.current_func
                    dist_name = func_name + "." + dist_name
                    if isinstance(src_type, dict):
                        self.np_list[dist_name] = src_type
                        self.np_list[dist_name]["scope"] = func_name
                    elif isinstance(src_type, str):
                        if "fixed" in src_type:
                            self.float_list[dist_name] = src_type
                            self.float_list[dist_name]["scope"] = func_name
                        elif "complex" in src_type:
                            self.complex_list[dist_name] = src_type
                            self.complex_list[dist_name]["scope"] = func_name

        self.generic_visit(node)


class ReturnAnalyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.return_var: dict[str, str] = {}
        self.function_stack: list[str] = []

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    def visit_Return(self, node: Return) -> Any:
        if isinstance(node.value, Name):
            func_name = self.function_stack[-1]
            id_name = node.value.id
            self.return_var[func_name] = id_name
        self.generic_visit(node)
