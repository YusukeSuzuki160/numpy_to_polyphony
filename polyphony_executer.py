# Standard Library
import logging
import os
from logging import getLogger

from polyphony_profiler import Profiler

from numpy_to_polyphony.library_generator import PythonGenerator, VerilogGenerator

TARGET_DIR = os.path.abspath("./target/") + "/"
PYTHON_DIR = os.path.abspath("./python-code/") + "/"
POLYPHONY_DIR = os.path.abspath("./polyphony-code/") + "/"
VERILOG_DIR = os.path.abspath("./verilog-code/") + "/"
ROOT = os.path.abspath("./") + "/"


class PolyphonyExecuter:
    def __init__(
        self,
        target: str,
        shapes: list[tuple[int, int]],
        config: str = "",
        profiler: Profiler = None,
    ) -> None:
        self.logger = getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(
            "./numpy_to_polyphony/.log/executer.log", mode="w"
        )
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.target = PYTHON_DIR + target + ".py"
        self.target_polyphony = POLYPHONY_DIR + target + ".polyphony.py"
        self.verilog_file = target + ".v"
        self.output = TARGET_DIR + target + ".out"
        self.command = (
            "polyphony"
            + " -o "
            + self.verilog_file
            + " -d"
            + VERILOG_DIR
            + " -D "
            + self.target_polyphony
        )
        if config != "":
            self.command += " -c " + config
            self.config = config
        self.test_command = "python3 " + self.target
        self.verilog_command = (
            "iverilog -o " + self.output + " " + "test.v " + self.verilog_file
        )
        self.shapes = shapes
        self.profiler = profiler

    def execute(self) -> None:
        os.system(self.test_command)
        self.logger.debug("command: " + self.test_command)
        PythonGenerator(self.shapes).generate()
        self.logger.debug("PythonGenerator(self.shapes).generate() called")
        if self.profiler is not None:
            self.profiler.process()
            self.logger.debug("profiler.process() called")
        os.system(self.command)
        self.logger.debug("command: " + self.command)
        VerilogGenerator(self.shapes).generate()
        self.logger.debug("VerilogGenerator().generate() called")
        # self.rewrite_top()
        self.logger.debug("rewrite_top() called")
        os.chdir(VERILOG_DIR)
        os.system(self.verilog_command)
        self.logger.debug("command: " + self.verilog_command)
        os.chdir(ROOT)
        os.system(self.output)
        self.logger.debug("command: " + self.output)
        if self.config:
            os.remove(self.config)

    def rewrite_top(self) -> None:
        verilog_file = VERILOG_DIR + self.verilog_file
        print(verilog_file)
        with open(verilog_file, mode="r") as f:
            lines = f.readlines()
        libs = ["complex_mult"]
        for lib in libs:
            lines.append('`include "' + lib + '.v"\n')
        with open(verilog_file, mode="w") as f:
            f.writelines(lines)
