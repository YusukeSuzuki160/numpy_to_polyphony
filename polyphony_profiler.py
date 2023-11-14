import ast
import cProfile
import os
import pstats
import re
import sys
from _ast import BinOp, Call, Expr
from typing import Any

Num = int | float | complex
RealNum = int | float
PROFILE_DIR = os.path.abspath("./profiles/") + "/"


class BinOpTrasslator(ast.NodeTransformer):
    def visit_BinOp(self, node: BinOp) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = node.op
        match op:
            case ast.Add:
                return ast.Call(
                    func=ast.Name(id="add", ctx=ast.Load()),
                    args=[left, right],
                    keywords=[],
                )
            case ast.Sub:
                return ast.Call(
                    func=ast.Name(id="sub", ctx=ast.Load()),
                    args=[left, right],
                    keywords=[],
                )
            case ast.Mult:
                return ast.Call(
                    func=ast.Name(id="mul", ctx=ast.Load()),
                    args=[left, right],
                    keywords=[],
                )
            case ast.Div:
                return ast.Call(
                    func=ast.Name(id="div", ctx=ast.Load()),
                    args=[left, right],
                    keywords=[],
                )
            case ast.FloorDiv:
                return ast.Call(
                    func=ast.Name(id="floordiv", ctx=ast.Load()),
                    args=[left, right],
                    keywords=[],
                )
            case ast.Mod:
                return ast.Call(
                    func=ast.Name(id="mod", ctx=ast.Load()),
                    args=[left, right],
                    keywords=[],
                )
            case ast.Pow:
                return ast.Call(
                    func=ast.Name(id="pow", ctx=ast.Load()),
                    args=[left, right],
                    keywords=[],
                )
            case _:
                return node


class Profiler:
    def __init__(self, code: str, filename: str) -> None:
        self.code = code
        self.filename = filename
        self.result = {}

    def process(self) -> None:
        tree = ast.parse(self.code)
        tree = BinOpTrasslator().visit(tree)
        self.code = ast.unparse(tree)

        def add(a: Num, b: Num) -> Num:
            return a + b

        def sub(a: Num, b: Num) -> Num:
            return a - b

        def mul(a: Num, b: Num) -> Num:
            return a * b

        def div(a: Num, b: Num) -> Num:
            return a / b

        def floordiv(a: RealNum, b: RealNum) -> RealNum:
            return a // b

        def mod(a: RealNum, b: RealNum) -> RealNum:
            return a % b

        def pow(a: Num, b: Num) -> Num:
            return a**b

        file_dir = os.path.dirname(self.filename)
        sys.path.append(file_dir)
        profiler = cProfile.Profile()
        profiler.enable()

        globals = {
            "__file__": self.filename,
            "__name__": "__main__",
            "__package__": None,
            "__cached__": None,
            "add": add,
            "sub": sub,
            "mul": mul,
            "div": div,
            "floordiv": floordiv,
            "mod": mod,
            "pow": pow,
        }

        exec(self.code, globals, None)

        profiler.disable()

        stats = pstats.Stats(profiler)
        stats.sort_stats("calls")
        stats.strip_dirs()

        profile_file = PROFILE_DIR + self.filename.split("/")[-1].split(".")[0] + ".prof"
        profiler.dump_stats(profile_file)
        profile_txt = PROFILE_DIR + self.filename.split("/")[-1].split(".")[0] + ".prof.txt"
        with open(profile_txt, mode="w") as f:
            for func, (cc, nc, tt, ct, callers) in stats.stats.items():
                file, line, func = func
                if func in ("<module>", "__main__", "__init__", "__new__"):
                    continue
                if file in (
                    "__init__.py",
                    "<frozen importlib._bootstrap>",
                    "<frozen importlib._bootstrap_external>",
                    "io.py",
                    "typing.py",
                    "queue.py",
                    "pathlib.py",
                    "__editable___polyphony_0_3_6_finder.py",
                    "machinery.py",
                    "<string>",
                    "_virtualenv.py",
                ):
                    continue
                if "str" in func:
                    continue
                if "__init__" in func:
                    continue
                if "__new__" in func:
                    continue
                if "built-in" in func:
                    continue
                func_name = f"{file}:{func}"
                self.result[func_name] = cc
                list_func_match = r"listc(\d+)r(\d+)\.([a-zA-Z0-9]+)"
                list_func_match_result = re.match(list_func_match, func)
                if list_func_match_result:
                    col = list_func_match_result.group(1)
                    row = list_func_match_result.group(2)
                    func_name = f"list {row} * {col} {list_func_match_result.group(3)}"
                f.write("{}: {}\n".format(func_name, cc))
