# Standard Library
import ast
from _ast import Add, Attribute, BinOp, Call, FunctionDef, Load, MatMult, Mult, Name, Sub
from typing import Any

# Third Party Library
from type_alias import VariableDict


class FunctionTranslator(ast.NodeTransformer):
    def __init__(
        self,
        array_list: VariableDict,
        np_list: VariableDict,
        float_list: VariableDict,
        complex_list: VariableDict,
        np_alias: str = "np",
    ) -> None:
        self.array_list = array_list
        self.np_list = np_list
        self.float_list = float_list
        self.complex_list = complex_list
        self.np_alias = np_alias
        self.lib_list = ["complex", "float"]
        self.shapes: list[tuple[int, ...]] = []
        self.current_func = ""

    def get_lib_list(self) -> list[str]:
        return self.lib_list

    def get_shapes(self) -> list[tuple[int, ...]]:
        return self.shapes

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.current_func = node.name
        self.generic_visit(node)
        return node

    def visit_Call(self, node: Call) -> Any:
        if isinstance(node.func, Attribute):
            if isinstance(node.func.value, Name) and node.func.value.id == "np":
                if node.func.attr == "array":
                    if isinstance(node.args[0], Name):
                        return node.args[0]
            elif isinstance(node.func.value, Attribute) and node.func.value.value.id == "np":
                if node.func.attr == "fft":
                    if isinstance(node.args[0], Name):
                        func_name = node.func.attr
                        arg_name = func_name + "." + node.args[0].id
                        if arg_name in self.array_list.keys():
                            shape = self.array_list[arg_name]["shape"]
                            col = shape[1]
                            row = shape[0]
                            dtype = self.array_list[arg_name]["dtype"]
                            attr_name = "list" + "c" + str(col) + "r" + str(row)
                            self.lib_list.append(attr_name)
                            self.shapes.append((col, row))
                            return ast.copy_location(
                                Call(
                                    func=Attribute(
                                        value=Name(id=attr_name, ctx=Load()),
                                        attr="fft",
                                        ctx=Load(),
                                    ),
                                    args=node.args,
                                    keywords=[],
                                ),
                                node,
                            )
                        elif arg_name in self.np_list.keys():
                            shape = self.np_list[arg_name]["shape"]
                            col = shape[1]
                            row = shape[0]
                            dtype = self.np_list[arg_name]["dtype"]
                            function_name = node.func.attr
                            attr_name = "list" + "c" + str(col) + "r" + str(row)
                            self.lib_list.append(attr_name)
                            self.shapes.append((col, row))
                            return ast.copy_location(
                                Call(
                                    func=Attribute(
                                        value=Name(id=attr_name, ctx=Load()),
                                        attr=function_name,
                                        ctx=Load(),
                                    ),
                                    args=node.args,
                                    keywords=[],
                                ),
                                node,
                            )

        elif (
            isinstance(node.func, Name) and node.func.id == "print" and isinstance(node.args, Name)
        ):  # print => listcxry._print
            func_name = node.func.id
            arg_name = func_name + "." + node.args.id
            shape = self.np_list[arg_name]["shape"]
            col = shape[1]
            row = shape[0]
            attr_name = "list" + "c" + str(col) + "r" + str(row)
            self.lib_list.append(attr_name)
            return Call(
                func=Attribute(value=Name(id=attr_name, ctx=Load()), attr="_print", ctx=Load()),
                args=node.args,
                keywords=[],
                starargs=None,
                kwargs=None,
            )
        else:
            return self.generic_visit(node)

    def visit_BinOp(self, node: BinOp) -> Any:
        left = node.left
        right = node.right
        left_name = self.current_func + "." + left.id
        right_name = self.current_func + "." + right.id
        if left_name not in self.np_list.keys() or right_name not in self.np_list.keys():
            if left_name in self.float_list.keys() and right_name in self.float_list.keys():
                return self.flaot_to_int(node)
            elif left_name in self.complex_list.keys() and right_name in self.complex_list.keys():
                ret_node = self.complex_to_int(node)
                if ret_node is not None:
                    return ret_node
                else:
                    return node
            else:
                return node
        if isinstance(left, ast.Name) and isinstance(right, ast.Name):
            left_shape = self.np_list[left_name]["shape"]
            right_shape = self.np_list[right_name]["shape"]
        dtype = self.np_list[left_name]["dtype"]
        function_name = ""
        left_col = left_shape[1]
        left_row = left_shape[0]
        attr_name = "list" + "c" + str(left_col) + "r" + str(left_row)
        self.lib_list.append(attr_name)
        self.shapes.append((left_col, left_row))
        args = [left, right]
        if isinstance(node.op, Add):
            function_name = "add"
        elif isinstance(node.op, Sub):
            function_name = "sub"
        elif isinstance(node.op, Mult):
            function_name = "mult"
        elif isinstance(node.op, MatMult):
            function_name = "matmult"
            col = right_shape[1]
            args.append(ast.Num(col))
        if function_name != "":
            return ast.copy_location(
                Call(
                    func=Attribute(
                        value=Name(id=attr_name, ctx=Load()),
                        attr=function_name,
                        ctx=Load(),
                    ),
                    args=args,
                    keywords=[],
                ),
                node,
            )

    def flaot_to_int(self, node: BinOp) -> Any:
        function_name = ""
        left_name = self.current_func + "." + node.left.id
        if isinstance(node.op, Add):
            function_name = "add"
        elif isinstance(node.op, Sub):
            function_name = "sub"
        elif isinstance(node.op, Mult):
            function_name = "mult"

        if function_name != "":
            return ast.copy_location(
                Call(
                    func=Attribute(
                        value=Name(id="float", ctx=Load()),
                        attr=function_name,
                        ctx=Load(),
                    ),
                    args=[node.left, node.right],
                    keywords=[],
                ),
                node,
            )

    def complex_to_int(self, node: BinOp) -> Call | None:
        function_name = ""
        left_name = self.current_func + "." + node.left.id
        if isinstance(node.op, Mult):
            function_name = "mult"
        else:
            return None

        args = [node.left, node.right]

        if function_name != "":
            return ast.copy_location(
                Call(
                    func=Attribute(
                        value=Name(id="complex", ctx=Load()),
                        attr=function_name,
                        ctx=Load(),
                    ),
                    args=args,
                    keywords=[],
                ),
                node,
            )
        else:
            return None
