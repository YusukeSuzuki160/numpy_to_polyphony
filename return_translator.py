import ast
import logging
from typing import Any

from type_alias import VariableDict


class ReturnTranslator(ast.NodeTransformer):
    def __init__(
        self,
        np_list: VariableDict,
        array_list: VariableDict,
        float_list: VariableDict,
        complex_list: VariableDict,
        return_var: VariableDict,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(
            "./numpy_to_polyphony/.log/return_translator.log", mode="w"
        )
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.debug("ReturnTranslator initialized")
        self.logger.debug("\n")
        self.np_list = np_list
        self.array_list = array_list
        self.float_list = float_list
        self.complex_list = complex_list
        self.return_var = return_var
        self.current_func = ""

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self.current_func = node.name
        self.generic_visit(node)
        return node

    def visit_Assign(self, node: ast.Assign) -> Any:
        if not isinstance(node.value, ast.Call):
            return self.generic_visit(node)
        dst = node.targets[0]
        self.generic_visit(node)
        func_name = self.current_func
        dst_name = func_name + "." + dst.id
        if self.return_var.get(func_name) == dst.id:
            call_args = node.value.args
            call_args.append(dst)
            node.value.args = call_args
            expr = ast.Expr(value= node.value)
            return [expr]
        else:
            if dst_name in self.np_list:
                shape = self.np_list[dst_name]["shape"]
                len = shape[0] * shape[1]
                dtype = self.np_list[dst_name]["dtype"]
                match dtype:
                    case "int64":
                        dec = ast.parse(f"{dst.id} = [0] * {len}")
                    case "float64":
                        dec = ast.parse(f"{dst.id} = [0.0] * {len}")
                    case "complex128":
                        dec = ast.parse(f"{dst.id} = [0] * {len}")
                    case _:
                        dec = ast.parse(f"{dst.id} = [0] * {len}")
                dec = dec.body[0]
                call_args = node.value.args
                call_args.append(dst)
                node.value.args = call_args
                expr = ast.Expr(value= node.value)
                return [dec, expr]
            elif dst_name in self.array_list:
                shape = self.array_list[dst_name]["shape"]
                len = shape[0] * shape[1]
                dtype = self.array_list[dst_name]["dtype"]
                match dtype:
                    case "int64":
                        dec = ast.parse(f"{dst.id} = [0] * {len}")
                    case "float64":
                        dec = ast.parse(f"{dst.id} = [0.0] * {len}")
                    case "complex128":
                        dec = ast.parse(f"{dst.id} = [0] * {len}")
                    case _:
                        dec = ast.parse(f"{dst.id} = [0] * {len}")
                dec = dec.body[0]
                call_args = node.value.args
                call_args.append(dst)
                node.value.args = call_args
                expr = ast.Expr(value= node.value)
                return [dec, expr]
            else:
                return self.generic_visit(node)