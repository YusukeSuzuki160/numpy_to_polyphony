# Standard Library
import ast
from _ast import Add, Attribute, BinOp, Call, Div, FunctionDef, Load, MatMult, Mult, Name, Sub
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
        self.lib_set = {"complex", "float"}
        self.shapes: set[tuple[int, ...]] = set()
        self.current_func = ""

    def get_lib_list(self) -> set[str]:
        return self.lib_set

    def get_shapes(self) -> set[tuple[int, ...]]:
        return self.shapes

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.current_func = node.name
        self.generic_visit(node)
        return node

    def visit_Call(self, node: Call) -> Any:
        if isinstance(node.func, Attribute):
            if isinstance(node.func.value, Name) and node.func.value.id == "np":
                if node.func.attr == "array":
                    if isinstance(node.args[0], Name) or isinstance(node.args[0], ast.List):
                        node = self.generic_visit(node)
                        return node.args[0]
                    else:
                        return self.generic_visit(node)
                elif node.func.attr == ("argsort"):
                    node = self.generic_visit(node)
                    func_name = self.current_func
                    arg_name = func_name + "." + node.args[0].id
                    shape = self.np_list[arg_name]["shape"]
                    col = shape[1]
                    row = shape[0]
                    attr_name = "list" + "c" + str(col) + "r" + str(row)
                    self.lib_set.add(attr_name)
                    self.shapes.add((col, row))
                    return ast.copy_location(
                        Call(
                            func=Attribute(
                                value=Name(id=attr_name, ctx=Load()),
                                attr=node.func.attr,
                                ctx=Load(),
                            ),
                            args=node.args,
                            keywords=[],
                        ),
                        node,
                    )
                elif node.func.attr == "cov":
                    node = self.generic_visit(node)
                    func_name = self.current_func
                    arg_name = func_name + "." + node.args[0].id
                    shape = self.np_list[arg_name]["shape"]
                    col = shape[1]
                    row = shape[0]
                    attr_name = "list" + "c" + str(col) + "r" + str(row)
                    self.lib_set.add(attr_name)
                    self.shapes.add((col, row))
                    rowvar = [kw for kw in node.keywords if kw.arg == "rowvar"]
                    if rowvar != []:
                        rowvar = rowvar[0].value
                    else:
                        rowvar = ast.NameConstant(value=True, kind=None)
                    return ast.copy_location(
                        Call(
                            func=Attribute(
                                value=Name(id=attr_name, ctx=Load()),
                                attr=node.func.attr,
                                ctx=Load(),
                            ),
                            args=node.args + [rowvar],
                            keywords=[],
                        ),
                        node,
                    )
                elif node.func.attr == "mean":
                    node = self.generic_visit(node)
                    axis = [kw for kw in node.keywords if kw.arg == "axis"]
                    func_name = self.current_func
                    arg_name = func_name + "." + node.args[0].id
                    shape = self.np_list[arg_name]["shape"]
                    col = shape[1]
                    row = shape[0]
                    attr_name = "list" + "c" + str(col) + "r" + str(row)
                    self.lib_set.add(attr_name)
                    self.shapes.add((col, row))
                    if len(axis) == 0:
                        return ast.copy_location(
                            Call(
                                func=Attribute(
                                    value=Name(id=attr_name, ctx=Load()),
                                    attr=node.func.attr,
                                    ctx=Load(),
                                ),
                                args=node.args,
                                keywords=[],
                            ),
                            node,
                        )
                    else:
                        axis = axis[0].value.n
                        return ast.copy_location(
                            Call(
                                func=Attribute(
                                    value=Name(id=attr_name, ctx=Load()),
                                    attr=node.func.attr + "_axis_" + str(axis),
                                    ctx=Load(),
                                ),
                                args=node.args,
                                keywords=[],
                            ),
                            node,
                        )

                else:
                    return self.generic_visit(node)
            elif isinstance(node.func.value, Attribute) and node.func.value.value.id == "np":
                if node.func.value.attr == "fft":
                    if isinstance(node.args[0], Name):
                        func_name = self.current_func
                        arg_name = func_name + "." + node.args[0].id
                        if arg_name in self.array_list.keys():
                            shape = self.array_list[arg_name]["shape"]
                            col = shape[1]
                            row = shape[0]
                            dtype = self.array_list[arg_name]["dtype"]
                            attr_name = "list" + "c" + str(col) + "r" + str(row)
                            function_name = node.func.attr
                            self.lib_set.add(attr_name)
                            self.shapes.add((col, row))
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
                        elif arg_name in self.np_list.keys():
                            shape = self.np_list[arg_name]["shape"]
                            col = shape[1]
                            row = shape[0]
                            dtype = self.np_list[arg_name]["dtype"]
                            function_name = node.func.attr
                            attr_name = "list" + "c" + str(col) + "r" + str(row)
                            self.lib_set.add(attr_name)
                            self.shapes.add((col, row))
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
                elif node.func.value.attr == "linalg":
                    if isinstance(node.args[0], Name):
                        func_name = self.current_func
                        arg_name = func_name + "." + node.args[0].id
                        if arg_name in self.array_list.keys():
                            shape = self.array_list[arg_name]["shape"]
                            col = shape[1]
                            row = shape[0]
                            dtype = self.array_list[arg_name]["dtype"]
                            attr_name = "list" + "c" + str(col) + "r" + str(row)
                            function_name = node.func.value.attr + "_" + node.func.attr
                            self.lib_set.add(attr_name)
                            self.shapes.add((col, row))
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
                        elif arg_name in self.np_list.keys():
                            shape = self.np_list[arg_name]["shape"]
                            col = shape[1]
                            row = shape[0]
                            dtype = self.np_list[arg_name]["dtype"]
                            function_name = node.func.value.attr + "_" + node.func.attr
                            attr_name = "list" + "c" + str(col) + "r" + str(row)
                            self.lib_set.add(attr_name)
                            self.shapes.add((col, row))
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
            self.lib_set.add(attr_name)
            self.shapes.add((col, row))
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
        self.lib_set.add(attr_name)
        self.shapes.add((left_col, left_row))
        args = [left, right]
        if isinstance(node.op, Add):
            if left_shape == right_shape:
                function_name = "add"
            else:
                if right_shape[0] == 1:
                    function_name = "add_horizontal"
                    args = [left, right]
                elif right_shape[1] == 1:
                    function_name = "add_vertical"
                    args = [left, right]
        elif isinstance(node.op, Sub):
            if left_shape == right_shape:
                function_name = "sub"
            else:
                if right_shape[0] == 1:
                    function_name = "sub_horizontal"
                    args = [left, right]
                elif right_shape[1] == 1:
                    function_name = "sub_vertical"
                    args = [left, right]
        elif isinstance(node.op, Mult):
            dtype = self.np_list[left_name]["dtype"]
            if dtype == "float64":
                function_name = "mult_float"
            else:
                function_name = "mult"
        elif isinstance(node.op, MatMult):
            dtype = self.np_list[left_name]["dtype"]
            if dtype == "float64":
                function_name = "matmult_float"
            else:
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

    def visit_Assign(self, node: ast.Assign) -> Any:
        if isinstance(node.value, ast.Subscript):
            target_shape = self.np_list[self.current_func + "." + node.targets[0].id]["shape"]
            target_col = target_shape[1]
            target_row = target_shape[0]
            if isinstance(node.value.slice, ast.Name):
                func_name = self.current_func
                arg_name = func_name + "." + node.value.slice.id
                shape = self.np_list[arg_name]["shape"]
                attr_name = "list" + "c" + str(target_col) + "r" + str(target_row)
                self.lib_set.add(attr_name)
                self.shapes.add((target_col, target_row))
                return ast.Assign(
                    targets=node.targets,
                    value=Call(
                        func=Attribute(
                            value=Name(id=attr_name, ctx=Load()),
                            attr="slice_by_array",
                            ctx=Load(),
                        ),
                        args=[node.value.value, node.value.slice],
                        keywords=[],
                    ),
                )
            elif isinstance(node.value.slice, ast.Tuple):
                func_name = self.current_func
                arg_name = func_name + "." + node.value.value.id
                shape = self.np_list[arg_name]["shape"]
                col = shape[1]
                row = shape[0]
                left = node.value.slice.elts[0]
                right = node.value.slice.elts[1]
                ret_stm = []
                left_arg = ""
                right_arg = ""
                if isinstance(left, ast.Slice):
                    lower = left.lower
                    upper = left.upper
                    if lower is None:
                        lower = 0
                    else:
                        lower = lower.n
                    if upper is None:
                        upper = row
                    else:
                        upper = upper.n
                    init_stm = "slice_left_" + arg_name.replace(".", "_") + " = " + "["
                    for i in range(lower, upper):
                        init_stm += str(i) + ","
                    init_stm = init_stm[:-1] + "]"
                    ret_stm.append(ast.parse(init_stm).body[0])
                    left_arg = "slice_left_" + arg_name.replace(".", "_")
                else:
                    left_arg = left.id
                if isinstance(right, ast.Slice):
                    lower = right.lower
                    upper = right.upper
                    if lower is None:
                        lower = 0
                    else:
                        if isinstance(lower, ast.Num):
                            lower = lower.n
                        elif isinstance(lower, ast.UnaryOp):
                            lower = col - lower.operand.n
                    if upper is None:
                        upper = col
                    else:
                        upper = upper.n
                    init_stm = "slice_right_" + arg_name.replace(".", "_") + " = " + "["
                    for i in range(lower, upper):
                        init_stm += str(i) + ","
                    init_stm = init_stm[:-1] + "]"
                    ret_stm.append(ast.parse(init_stm).body[0])
                    right_arg = "slice_right_" + arg_name.replace(".", "_")
                else:
                    right_arg = right.id
                attr_name = "list" + "c" + str(target_col) + "r" + str(target_row)
                self.lib_set.add(attr_name)
                self.shapes.add((target_col, target_row))
                ret_stm.append(
                    ast.Assign(
                        targets=node.targets,
                        value=Call(
                            func=Attribute(
                                value=Name(id=attr_name, ctx=Load()),
                                attr="slice_by_tuple",
                                ctx=Load(),
                            ),
                            args=[
                                node.value.value,
                                Name(id=left_arg, ctx=Load()),
                                Name(id=right_arg, ctx=Load()),
                            ],
                            keywords=[],
                        ),
                    )
                )
                return ret_stm
            else:
                return self.generic_visit(node)
        else:
            return self.generic_visit(node)

    def flaot_to_int(self, node: BinOp) -> Any:
        function_name = ""
        left_name = self.current_func + "." + node.left.id
        if isinstance(node.op, Add):
            return self.generic_visit(node)
        elif isinstance(node.op, Sub):
            return self.generic_visit(node)
        elif isinstance(node.op, Mult):
            function_name = "mult"
        elif isinstance(node.op, Div):
            function_name = "div"

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
