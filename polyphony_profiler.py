import ast
import cProfile
import json
import logging
import math
import os
import pstats
import re
import sys
import time
import types
from _ast import BinOp, Constant, Import
from ast import Num
from logging import getLogger
from typing import Any, Callable

import astor
import numpy as np
from type_alias import VariableDict

Num = int | float | complex
RealNum = int | float
PROFILE_DIR = os.path.abspath("./profiles/") + "/"


class CountedNumber:
    # 四則演算のカウンタ
    add_count = 0
    sub_count = 0
    mul_count = 0
    div_count = 0
    mod_count = 0
    pow_count = 0

    def __init__(self, value):
        self.value = value

    def __add__(self, other):
        CountedNumber.add_count += 1
        if isinstance(other, CountedNumber):
            return CountedNumber(self.value + other.value)
        else:
            return CountedNumber(self.value + other)

    def __sub__(self, other):
        CountedNumber.sub_count += 1
        if isinstance(other, CountedNumber):
            return CountedNumber(self.value - other.value)
        else:
            return CountedNumber(self.value - other)

    def __mul__(self, other):
        CountedNumber.mul_count += 1
        if isinstance(other, CountedNumber):
            return CountedNumber(self.value * other.value)
        else:
            return CountedNumber(self.value * other)

    def __truediv__(self, other):
        CountedNumber.div_count += 1
        if isinstance(other, CountedNumber):
            return CountedNumber(self.value / other.value)
        else:
            return CountedNumber(self.value / other)

    def __floordiv__(self, other):
        CountedNumber.div_count += 1
        if isinstance(other, CountedNumber):
            return CountedNumber(self.value // other.value)
        else:
            return CountedNumber(self.value // other)

    def __mod__(self, other):
        CountedNumber.mod_count += 1
        if isinstance(other, CountedNumber):
            return CountedNumber(self.value % other.value)
        else:
            return CountedNumber(self.value % other)

    def __pow__(self, other):
        CountedNumber.pow_count += 1
        if isinstance(other, CountedNumber):
            return CountedNumber(self.value**other.value)
        else:
            return CountedNumber(self.value**other)

    def __eq__(self, other):
        if isinstance(other, CountedNumber):
            return self.value == other.value
        else:
            return self.value == other

    def __ne__(self, other):
        if isinstance(other, CountedNumber):
            return self.value != other.value
        else:
            return self.value != other

    def __lt__(self, other):
        if isinstance(other, CountedNumber):
            return self.value < other.value
        else:
            return self.value < other

    def __le__(self, other):
        if isinstance(other, CountedNumber):
            return self.value <= other.value
        else:
            return self.value <= other

    def __gt__(self, other):
        if isinstance(other, CountedNumber):
            return self.value > other.value
        else:
            return self.value > other

    def __ge__(self, other):
        if isinstance(other, CountedNumber):
            return self.value >= other.value
        else:
            return self.value >= other

    def __neg__(self):
        return CountedNumber(-self.value)

    def __pos__(self):
        return CountedNumber(+self.value)

    def __abs__(self):
        return CountedNumber(abs(self.value))

    def __invert__(self):
        return CountedNumber(~self.value)

    def __round__(self, n=None):
        return CountedNumber(round(self.value, n))

    def __floor__(self):
        return CountedNumber(math.floor(self.value))

    def __ceil__(self):
        return CountedNumber(math.ceil(self.value))

    def __trunc__(self):
        return CountedNumber(math.trunc(self.value))

    def __rshift__(self, other):
        if isinstance(other, CountedNumber):
            return CountedNumber(self.value >> other.value)
        else:
            return CountedNumber(self.value >> other)

    def __lshift__(self, other):
        if isinstance(other, CountedNumber):
            return CountedNumber(self.value << other.value)
        else:
            return CountedNumber(self.value << other)

    def __rrshift__(self, other):
        if isinstance(other, CountedNumber):
            return CountedNumber(other.value >> self.value)
        else:
            return CountedNumber(other >> self.value)

    def __rlshift__(self, other):
        if isinstance(other, CountedNumber):
            return CountedNumber(other.value << self.value)
        else:
            return CountedNumber(other << self.value)

    def __and__(self, other):
        return CountedNumber(self.value & other.value)

    def __or__(self, other):
        return CountedNumber(self.value | other.value)

    def __xor__(self, other):
        return CountedNumber(self.value ^ other.value)

    def __radd__(self, other):
        return other + self.value

    def __rsub__(self, other):
        return other - self.value

    def __rmul__(self, other):
        if isinstance(other, list):
            return other * self.value
        elif isinstance(other, int):
            return other * self.value
        raise TypeError(
            "Unsupported operand type(s) for *: 'CountedNumber' and '{}'".format(
                type(other).__name__
            )
        )

    def __rtruediv__(self, other):
        return other / self.value

    def __rfloordiv__(self, other):
        return other // self.value

    def __rmod__(self, other):
        return other % self.value

    def __rpow__(self, other):
        return other**self.value

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __complex__(self):
        return complex(self.value)

    def __bool__(self):
        return bool(self.value)

    def __index__(self):
        return self.value

    def __repr__(self):
        return str(self.value)


class NumTransformer(ast.NodeTransformer):
    def visit_Constant(self, node: Constant) -> Any:
        value = node.value
        return ast.Call(
            func=ast.Name(id="CountedNumber", ctx=ast.Load()),
            args=[ast.Constant(value=value)],
            keywords=[],
        )

    def visit_Num(self, node: Num) -> Any:
        value = node.n
        return ast.Call(
            func=ast.Name(id="CountedNumber", ctx=ast.Load()),
            args=[ast.Constant(value=value)],
            keywords=[],
        )


class Profiler:
    def __init__(
        self,
        code: str,
        filename: str,
        lib_list: list[str],
    ) -> None:
        self.code = code
        self.filename = filename
        self.result: dict[str, Any] = {}
        self.lib_list = lib_list

    def process(self) -> None:
        logger = getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler("./numpy_to_polyphony/.log/profiler.log", mode="w")
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        tree = ast.parse(self.code)
        logger.debug("tree:\n%s", astor.dump_tree(tree))
        num_transformer = NumTransformer()
        tree = num_transformer.visit(tree)
        self.code = ast.unparse(tree)
        logger.debug("code:\n%s", self.code)
        lib_path = os.path.abspath("./polyphony-code/")
        sys.path.append("./numpy_to_polyphony/")
        preprocessed_code = {}
        for lib in self.lib_list:
            lib_path += "/" + lib + ".py"
            logger.debug("lib_path: %s", lib_path)
            with open(lib_path) as f:
                lib_code = f.read()
            lib_tree = ast.parse(lib_code)
            logger.debug("lib_tree before:\n%s", astor.dump_tree(lib_tree))
            lib_tree = num_transformer.visit(lib_tree)
            logger.debug("lib_tree after:\n%s", astor.dump_tree(lib_tree))
            lib_code = ast.unparse(lib_tree)
            logger.debug("lib_code:\n%s", lib_code)
            lib_code = "from polyphony_profiler import CountedNumber\n" + lib_code
            with open(lib_path, "w") as f:
                f.write(lib_code)
            lib_path = os.path.abspath("./polyphony-code/")

        file_dir = os.path.dirname(self.filename)
        sys.path.append(file_dir)
        globals = {
            "__file__": self.filename,
            "__name__": "__main__",
            "__package__": None,
            "__cached__": None,
            "CountedNumber": CountedNumber,
        }

        # for import_stm in self.import_list:
        #     exec(import_stm, globals, None)

        # for function_def in function_defs:
        #     exec(function_def, globals, None)

        # for func in self.call_func_list:
        #     exec(f"{func} = count_calls({func})", globals, None)
        profiler = cProfile.Profile()
        profiler.enable()

        start_time = time.time()
        exec(self.code, globals, None)
        end_time = time.time()

        # for func in self.call_func_list:
        #     exec(f'call_nums["{func}"] = {func}.calls', globals, None)
        profiler.disable()

        stats = pstats.Stats(profiler)
        stats.sort_stats("calls")
        stats.strip_dirs()

        profile_txt = PROFILE_DIR + self.filename.split("/")[-1].split(".")[0] + ".prof.json"
        profile_for_debug = PROFILE_DIR + self.filename.split("/")[-1].split(".")[0] + ".prof.txt"
        calculation = end_time - start_time
        exclusive_func = [
            "print",
            "np.array",
            "test",
            "main",
            "range",
            "broadcast_to",
            "may_share_memory",
            "result_type",
            "iterable",
            "__init__",
            "__rmul__",
            "__index__",
            "__int__",
            "__repr__",
            "__str__",
            "<module>",
            "__int__",
            "__float__",
            "__complex__",
            "__bool__",
        ]
        with open(profile_for_debug, "w") as f:
            f.write(f"calculation time: {calculation}\n")
            for func, (cc, nc, tt, ct, callers) in stats.stats.items():
                file, line, func = func
                # if file in use_files:)
                if file.split(".")[0] in self.lib_list or file in ["polyphony_profiler.py"]:
                    if func in exclusive_func:
                        continue
                    f.write(f"{func} at {file}: {cc}\n")
                    if file == "polyphony_profiler.py":
                        file = ""
                    else:
                        file = file.split(".")[0] + "."
                    self.result[file + func] = {
                        "call count": cc,
                        "total time percent (%)": tt / calculation * 100,
                    }
        del_keys = []
        for key, value in self.result.items():
            match key:
                case "__radd__":
                    self.result["__add__"]["call count"] += value["call count"]
                    self.result["__add__"]["total time percent (%)"] += value[
                        "total time percent (%)"
                    ]
                case "__rsub__":
                    self.result["__sub__"]["call count"] += value["call count"]
                    self.result["__sub__"]["total time percent (%)"] += value[
                        "total time percent (%)"
                    ]
                case "__rmul__":
                    self.result["__mul__"]["call count"] += value["call count"]
                    self.result["__mul__"]["total time percent (%)"] += value[
                        "total time percent (%)"
                    ]
                case "__rtruediv__":
                    self.result["__truediv__"]["call count"] += value["call count"]
                    self.result["__truediv__"]["total time percent (%)"] += value[
                        "total time percent (%)"
                    ]
                case "__rfloordiv__":
                    self.result["__floordiv__"]["call count"] += value["call count"]
                    self.result["__floordiv__"]["total time percent (%)"] += value[
                        "total time percent (%)"
                    ]
                case "__rmod__":
                    self.result["__mod__"]["call count"] += value["call count"]
                    self.result["__mod__"]["total time percent (%)"] += value[
                        "total time percent (%)"
                    ]
                case "__rpow__":
                    self.result["__pow__"]["call count"] += value["call count"]
                    self.result["__pow__"]["total time percent (%)"] += value[
                        "total time percent (%)"
                    ]
                case "__rlshift__":
                    self.result["__lshift__"]["call count"] += value["call count"]
                    self.result["__lshift__"]["total time percent (%)"] += value[
                        "total time percent (%)"
                    ]
                case "__rrshift__":
                    self.result["__rshift__"]["call count"] += value["call count"]
                    self.result["__rshift__"]["total time percent (%)"] += value[
                        "total time percent (%)"
                    ]
                case "__rand__":
                    self.result["__and__"]["call count"] += value["call count"]
                    self.result["__and__"]["total time percent (%)"] += value[
                        "total time percent (%)"
                    ]
                case "__ror__":
                    self.result["__or__"]["call count"] += value["call count"]
                    self.result["__or__"]["total time percent (%)"] += value[
                        "total time percent (%)"
                    ]
                case "__rxor__":
                    self.result["__xor__"]["call count"] += value["call count"]
                    self.result["__xor__"]["total time percent (%)"] += value[
                        "total time percent (%)"
                    ]
                case "__rmatmul__":
                    self.result["__matmul__"]["call count"] += value["call count"]
                    self.result["__matmul__"]["total time percent (%)"] += value[
                        "total time percent (%)"
                    ]
                case _:
                    continue
            del_keys.append(key)
        for key in del_keys:
            del self.result[key]
        with open(profile_txt, "w") as f:
            json.dump(self.result, f, indent=4)
