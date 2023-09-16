import logging
import os
from logging import getLogger

import polyphony_lib.generate as plib

SRC_PATH = os.path.abspath("./numpy_to_polyphony/verilog/") + "/"
DST_PATH = os.path.abspath("./verilog-code/") + "/"
PYTHON_PATH = os.path.abspath("./python-code/") + "/"
GENERATE_FILE = ["complex_mult.v", "float_mult.v"]
LIB_PATH = os.path.abspath("./numpy_to_polyphony/polyphony_lib/") + "/"


class VerilogGenerator:
    def __init__(self) -> None:
        self.logger = getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(
            "./numpy_to_polyphony/.log/verilog_generator.log", mode="w"
        )
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.debug("VerilogGenerator initialized")
        self.logger.debug("\n")

    def generate(self) -> None:
        for filename in GENERATE_FILE:
            src = SRC_PATH + filename
            dst = DST_PATH + filename
            with open(src, mode="r") as f:
                data = f.read()
            with open(dst, mode="w") as f:
                f.write(data)
            self.logger.debug("generated: " + dst)
            self.logger.debug("\n")


class PythonGenerator:
    def __init__(self, shapes: list[tuple[int, int]]) -> None:
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

    def generate(self) -> None:
        plib.generate(self.shapes)
        os.system("cp -R " + LIB_PATH + "*" + " " + PYTHON_PATH)
        self.logger.debug("plib.generate called")
        self.logger.debug("\n")
