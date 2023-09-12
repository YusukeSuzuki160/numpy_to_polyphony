# Standard Library
import ast
from _ast import (
    AnnAssign,
    Assign,
    Attribute,
    Call,
    Expr,
    FunctionDef,
    Import,
    Load,
    Name,
    Return,
    Subscript,
)
from typing import Any

# Third Party Library
from parse_complex import Complex
from type_alias import VariableDict


class LastTranslator(ast.NodeTransformer):
    def __init__(
        self,
        arrat_list: VariableDict,
        float_list: VariableDict,
        complex_list: VariableDict,
        np_list: VariableDict,
        return_var: VariableDict,
        return_type: VariableDict,
    ) -> None:
        self.precision = 16
        self.array_list = arrat_list
        self.float_list = float_list
        self.complex_list = complex_list
        self.np_list = np_list
        self.return_var = return_var
        self.return_type = return_type
        self.nonreturn_func = ["complex", "float"]
        self.current_func = ""
        self.is_return = False

    def visit_Import(self, node: Import) -> Any:
        if node.names[0].name == "numpy":
            self.generic_visit(node)
            return None
        else:
            self.generic_visit(node)
            return node

    def visit_Num(self, node: ast.Num) -> Any:
        if isinstance(node.n, float):
            num = self.fixed_to_int(node.n)
            return ast.Num(n=num)
        elif isinstance(node.n, complex):
            imag = node.n.imag
            if isinstance(imag, float):
                imag = self.fixed_to_int(imag)
            return ast.Num(n=imag)
        else:
            return node

    def visit_Return(self, node: Return) -> Any:
        if self.is_return:
            self.is_return = False
            return self.generic_visit(node)
        else:
            return None

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.current_func = node.name
        if node.name in self.return_var.keys():
            return_var = self.return_var[node.name]
            var_full = node.name + "." + return_var
            if var_full in self.float_list.keys() or var_full in self.complex_list.keys():
                self.is_return = True
                return self.generic_visit(node)
            node.args.args.append(ast.arg(arg=return_var, annotation=None))
        self.generic_visit(node)
        return node

    def visit_Assign(self, node: Assign) -> Any:
        if isinstance(node.targets[0], Name):
            func_name = self.current_func
            var_name = func_name + "." + node.targets[0].id
            value = self.visit(node.value)
            if var_name in self.complex_list.keys():
                return AnnAssign(
                    target=node.targets[0],
                    annotation=Name(id="int64", ctx=Load()),
                    value=value,
                    simple=1,
                )
            else:
                return self.generic_visit(node)
        elif isinstance(node.value, Call):
            if not isinstance(node.targets[0], Name):
                return self.generic_visit(node)  # TODO: fix
            return_var = node.targets[0].id
            if (
                isinstance(node.value.func, Attribute)
                and isinstance(node.value.func.value, Name)
                and node.value.func.value.id in self.nonreturn_func
            ):
                return self.generic_visit(node)
            else:
                node.value.args.append(Name(id=return_var, ctx=Load()))
                new_stm = Expr(value=node.value)
                if return_var in self.np_list and return_var not in self.return_var.values():
                    return_var_scope = self.current_func + "." + return_var
                    shape = self.np_list[return_var_scope]["shape"]
                    assert isinstance(shape, list)
                    len = shape[0] * shape[1]
                    init_stm = ast.parse(return_var + " = [0] * " + str(len)).body[0]
                    return [init_stm, new_stm]
                else:
                    return new_stm
        else:
            return self.generic_visit(node)

    def visit_Subscript(self, node: Subscript) -> Any:
        if isinstance(node.value, Subscript):
            if isinstance(node.value.value, Name):
                func_name = self.current_func
                id_name = func_name + "." + node.value.value.id
                if id_name in self.np_list.keys():
                    shape = self.np_list[id_name]["shape"]
                    col = shape[1]
                    index = ast.BinOp(
                        left=ast.BinOp(
                            left=node.value.slice,
                            op=ast.Mult(),
                            right=ast.Num(n=col),
                        ),
                        op=ast.Add(),
                        right=node.slice,
                    )
                    return Subscript(
                        value=Name(id=node.value.value.id),
                        slice=index,
                        ctx=node.ctx,
                    )
        return node

    def visit_Complex(self, node: Complex) -> Any:
        real = self.visit(node.real)
        imag = self.visit(node.imag)
        num = real.n << 32 | imag.n
        return ast.Num(n=num)

    def fixed_to_int(self, number: float) -> int:
        return int(number * (1 << self.precision))
