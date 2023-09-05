import logging
import os
from logging import getLogger

SRC_PATH = os.path.abspath("./numpy_to_polyphony/verilog/") + "/"
DST_PATH = os.path.abspath("./verilog-code/") + "/"
GENERATE_FILE = ["complex_mult.v"]
PREFIX = "numpy_to_polyphony_polyphony_lib_"


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
            dst = DST_PATH + PREFIX + filename
            with open(src, mode="r") as f:
                data = f.read()
            with open(dst, mode="w") as f:
                f.write(data)
            self.logger.debug("generated: " + dst)
            self.logger.debug("\n")
