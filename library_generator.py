import ast
import logging
import os
from logging import getLogger

import astor
import polyphony_lib.generate as plib
from analyzer import ImmidiateAssignAnalyzer
from hdlmodule import (
    HDLBlockingAssign,
    HDLIfElse,
    HDLIndexAccess,
    HDLModule,
    HDLNonBlockingAssign,
    HDLVariable,
)
from type_alias import Number

from division_optimizer import DivisionOptimizer

SRC_PATH = os.path.abspath("./numpy_to_polyphony/verilog/") + "/"
DST_PATH = os.path.abspath("./verilog-code/") + "/"
PYTHON_PATH = os.path.abspath("./python-code/") + "/"
POLYPHONY_PATH = os.path.abspath("./polyphony-code/") + "/"
GENERATE_FILE = ["complex_mult.v", "float_mult.v"]
LIB_PATH = os.path.abspath("./numpy_to_polyphony/polyphony_lib/") + "/"


class VerilogGenerator:
    def __init__(self, shapes: list[tuple[int, int]]) -> None:
        self.logger = getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(
            "./numpy_to_polyphony/.log/verilog_generator.log", mode="w"
        )
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.debug("VerilogGenerator initialized")
        self.logger.debug("\n")
        self.shapes = shapes

    def generate(self) -> None:
        # self.generate_matmult()
        for filename in GENERATE_FILE:
            src = SRC_PATH + filename
            dst = DST_PATH + filename
            with open(src, mode="r") as f:
                data = f.read()
            with open(dst, mode="w") as f:
                f.write(data)
            self.logger.debug("generated: " + dst)
            self.logger.debug("\n")

    def generate_matmult(self) -> None:  # TODO: implement matmult for not square matrix
        for col, row in self.shapes:
            module_name = "list" + "c" + str(col) + "r" + str(row) + "_matmult"
            module = HDLModule(module_name)
            for i in range(col * row):
                module.add_port("matmult_in_a" + str(i), 64, "input wire", signed=True)
            for i in range(col * row):
                module.add_port(
                    "matmult_out_a" + str(i), 64, "output wire", signed=True
                )
            for i in range(col * row):
                module.add_port("matmult_in_b" + str(i), 64, "input wire", signed=True)
            for i in range(col * row):
                module.add_port(
                    "matmult_out_b" + str(i), 64, "output wire", signed=True
                )
            module.add_port("matmult_in_col", 8, "input wire")
            for i in range(row * row):
                module.add_port("matmult_in_c" + str(i), 64, "input wire", signed=True)
            for i in range(row * row):
                module.add_port(
                    "matmult_out_c" + str(i), 64, "output wire", signed=True
                )
            module.add_list("a", 64, col * row, signed=True)
            module.add_list("b", 64, col * row, signed=True)
            module.add_list("c", 64, col * row, signed=True)
            input_state = HDLIfElse()
            for i in range(col * row):
                input_state.add_action(
                    "matmult_ready",
                    HDLNonBlockingAssign(
                        HDLIndexAccess("a", i), "matmult_in_a" + str(i)
                    ),
                )
            for i in range(col * row):
                input_state.add_action(
                    "matmult_ready",
                    HDLNonBlockingAssign(
                        HDLIndexAccess("b", i), "matmult_in_b" + str(i)
                    ),
                )
            module.add_dataflow("idle", input_state)
            for i in range(row * row):
                calc = ""
                for j in range(col):
                    calc += "a[" + str(i // row * col + j) + "] * "
                    calc += "b[" + str(i % row + j * row) + "] + "
                calc = calc[:-3]
                module.add_dataflow(
                    "calc",
                    HDLNonBlockingAssign(HDLIndexAccess("c", i), calc),
                )
            for i in range(row * row):
                module.add_assign("matmult_out_c" + str(i), HDLIndexAccess("c", i))
            module.add_controlflow("idle", "matmult_ready", "calc")
            module.add_controlflow("calc", "1", "fin")
            module.generate()
            GENERATE_FILE.append(module_name + ".v")


class PythonGenerator:
    def __init__(self, shapes: list[tuple[int, int]], number_list: dict[str, Number]) -> None:
        self.logger = getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(
            "./numpy_to_polyphony/.log/python_generator.log", mode="w"
        )
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.debug("PythonGenerator initialized")
        self.logger.debug("\n")
        self.shapes = shapes
        self.number_list = number_list

    def generate(self) -> None:
        plib.generate(self.shapes)
        os.system("cp -R " + LIB_PATH + "*" + " " + POLYPHONY_PATH)
        self.logger.debug("plib.generate called")
        self.logger.debug("\n")
        for col, row in self.shapes:
            filename = "list" + "c" + str(col) + "r" + str(row)
            self.translate_lib(filename)
        self.logger.debug("division_optimizer called called")

    def translate_lib(self, lib_name: str) -> None:
        code = open(POLYPHONY_PATH + lib_name + ".py").read()
        tree = ast.parse(code)
        self.logger.debug("tree in ast.parse:\n%s", astor.dump_tree(tree))
        analyzer = ImmidiateAssignAnalyzer()
        analyzer.visit(tree)
        number_list = analyzer.number_list
        globals = analyzer.globals
        optimizer = DivisionOptimizer(number_list, globals=globals)
        optimizer.visit(tree)
        self.logger.debug("tree in DivisionOptimizer:\n%s", astor.dump_tree(tree))
        source = ast.unparse(tree)
        output_file = POLYPHONY_PATH + lib_name + ".py"
        with open(output_file, "w") as f:
            f.write(source)
