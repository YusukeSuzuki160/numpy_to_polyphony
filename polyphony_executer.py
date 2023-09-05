# Standard Library
import logging
import os
from logging import getLogger

from verilog_generator import VerilogGenerator

TARGET_DIR = os.path.abspath("./target/") + "/"
PYTHON_DIR = os.path.abspath("./python-code/") + "/"
VERILOG_DIR = os.path.abspath("./verilog-code/") + "/"
ROOT = os.path.abspath("./") + "/"


class PolyphonyExecuter:
    def __init__(self, target: str):
        self.logger = getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler("./numpy_to_polyphony/.log/executer.log", mode="w")
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.target = PYTHON_DIR + target + ".py"
        self.target_polyphony = PYTHON_DIR + target + ".polyphony.py"
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
        self.test_command = "python3 " + self.target
        self.verilog_command = "iverilog -o " + self.output + " " + "test.v " + self.verilog_file

    def execute(self) -> None:
        os.system(self.test_command)
        self.logger.debug("command: " + self.test_command)
        os.system(self.command)
        self.logger.debug("command: " + self.command)
        VerilogGenerator().generate()
        self.logger.debug("VerilogGenerator().generate() called")
        os.chdir(VERILOG_DIR)
        os.system(self.verilog_command)
        self.logger.debug("command: " + self.verilog_command)
        os.chdir(ROOT)
        os.system(self.output)
        self.logger.debug("command: " + self.output)
