import ast
import logging
from _ast import AST, Assign, FunctionDef
from logging import getLogger
from typing import Any

import astor
import numpy as np

np.set_printoptions(threshold=np.inf)


class PureExecuter(ast.NodeTransformer):
    def __init__(self) -> None:
        self.logger = getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler("./numpy_to_polyphony/.log/pure_executer.log", mode="w")
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.debug("PureExecuter")
        self.func_ret: dict[str, Any] = {}

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        is_exec = False
        if node.decorator_list:
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name) and decorator.id == "pure":
                    node.decorator_list.remove(decorator)
                    is_exec = True
                    break

        self.logger.debug("is_exec: %s", is_exec)

        if is_exec:
            exec_node = ast.parse(ast.unparse(node))
            self.logger.debug("exec_node:\n%s", astor.dump_tree(exec_node))
            compiled_code = compile(exec_node, filename="<ast>", mode="exec")
            exec(compiled_code, globals(), locals())
            function_name = node.name
            func_ref = locals()[function_name]
            ret = func_ref()
            if isinstance(ret, np.ndarray):
                ret = ret.tolist()
                ret = ast.parse(str(ret)).body[0].value
                self.func_ret[function_name] = ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id="np", ctx=ast.Load()), attr="array", ctx=ast.Load()
                    ),
                    args=[ret],
                    keywords=[],
                )
            elif isinstance(ret, list):
                ret = ast.parse(str(ret)).body[0].value
                self.func_ret[function_name] = ret
            else:
                self.func_ret[function_name] = ast.Constant(value=ret)
            return
        else:
            return self.generic_visit(node)

    def visit_Assign(self, node: Assign) -> Any:
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                func_name = node.value.func.id
                if func_name in self.func_ret.keys():
                    node.value = self.func_ret[func_name]
                    return node
        return self.generic_visit(node)
