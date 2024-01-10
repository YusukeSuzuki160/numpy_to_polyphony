import logging
import os
from logging import getLogger
from typing import Any

import pandas as pd

RealNum = int | float
PROFILE_DIR = os.path.abspath("./profiles/") + "/"
PYTHON_DIR = os.path.abspath("./python-code/") + "/"


class ProfileResultSorter:
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.df: Any = None

    def __load_profile_result(self) -> None:
        colspecs = [(0, 6), (7, 16), (17, 25), (26, 34), (35, 43), (44, 52), (52, 100)]
        self.df = pd.read_fwf(self.filename, colspecs=colspecs)

    def __chenge_column_name_unique(self) -> None:
        self.df.columns = [
            "time",
            "cum_seconds",
            "self_seconds",
            "calls",
            "us/call",
            "us/call_total",
            "name",
        ]

    def __sort_by_time_per_one(self) -> None:
        self.df = self.df.sort_values(by=["us/call_total"], ascending=False)

    def __sort_by_time(self) -> None:
        self.df = self.df.sort_values(by=["us/call"], ascending=False)

    def __sort_by_calls(self) -> None:
        self.df = self.df.sort_values(by=["calls"], ascending=False)

    def process(self) -> None:
        self.__load_profile_result()
        self.__chenge_column_name_unique()
        # self.__select_UFunc()
        self.__sort_by_time_per_one()
        output_filename = self.filename.split("/")[-1].split(".")[0] + ".txt"
        output_str = self.df.to_string(index=False)
        with open(PROFILE_DIR + output_filename, "w") as f:
            f.write(output_str)


class Profiler:
    def __init__(
        self,
        code: str,
        filename: str,
    ) -> None:
        self.code = code
        self.filename = filename
        self.result: dict[str, Any] = {}
        self.original_code = code
        # commands for profiling
        current_path = os.path.abspath("./")
        self.numpy_path = current_path + "/numpy/build/numpy/"
        self.run_command = (
            "../cpython/python.exe -m spin run ../cpython/python.exe " + PYTHON_DIR + self.filename + ".py"
        )
        self.umath_so = self.numpy_path + "core/_multiarray_umath.cpython-310-aarch64-linux-gnu.so"
        self.linalg_so = self.numpy_path + "linalg/_umath_linalg.cpython-310-aarch64-linux-gnu.so"
        self.get_flat_profile_command = "sed -n '/Flat profile:/,/granularity:/p' | sed '/granularity:/d' |tail -n +5|  head -n -37"
        self.gprof_out = PROFILE_DIR + self.filename.split("/")[-1].split(".")[0] + "_np.prof.txt"
        self.gprof_linalg_out = (
            PROFILE_DIR + self.filename.split("/")[-1].split(".")[0] + "_np_linalg.prof.txt"
        )
        self.gprof_command = (
            "gprof "
            + self.umath_so
            + "|"
            + self.get_flat_profile_command
            + "> "
            + PROFILE_DIR
            + self.filename.split("/")[-1].split(".")[0]
            + "_np.prof.txt"
        )

        self.gprof_linalg_command = (
            "gprof "
            + self.linalg_so
            + "|"
            + self.get_flat_profile_command
            + "> "
            + PROFILE_DIR
            + self.filename.split("/")[-1].split(".")[0]
            + "_np_linalg.prof.txt"
        )

    def process(self) -> None:
        logger = getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler("./numpy_to_polyphony/.log/profiler.log", mode="w")
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        logger.debug("code:\n%s", self.code)
        self.code = (
            "import cProfile\nimport pstats\nprofiler = cProfile.Profile()\nprofiler.enable()\n"
            + self.code
            + "\nprofiler.disable()\n"
            + "stats = pstats.Stats(profiler)\n"
            + "stats_list = stats.stats.items()\n"
            + "sorted_stats = sorted(stats_list, key=lambda x: x[1][3]/x[1][0] if x[1][0] else 0, reverse=True)\n"
            + "output_file = '"
            + PROFILE_DIR
            + self.filename.split("/")[-1].split(".")[0]
            + ".prof.txt'\n"
            + "with open (output_file, 'w') as f:\n"
            + '    print(f\'{"ncalls":>7} {"tottime":>10} {"percall":>10} {"cumtime":>10} {"percall":>10}    {"Function":<40}\', file=f)\n'
            + "    for func, stat in sorted_stats:\n"
            + "        cc, nc, tt, ct, callers = stat\n"
            + "        file, line, func = func\n"
            + "        func = f'{file}:{func}'\n"
            + "        pc1 = tt / nc if nc else 0\n"
            + "        pc2 = ct / cc if cc else 0\n"
            + "        print(f'{nc:>7} {tt:>10.5f} {pc1:>10.5f} {ct:>10.5f} {pc2:>10.5f}    {func:<40}', file=f)\n"
        )
        logger.debug("code:\n%s", self.code)
        with open(PYTHON_DIR + self.filename + ".py", "w") as f:
            f.write(self.code)
        logger.debug("filename:\n%s", self.filename)
        os.chdir("./numpy/")
        logger.debug("os.getcwd():\n%s", os.getcwd())
        os.system(self.run_command)
        logger.debug("run_command:\n%s", self.run_command)
        os.system(self.gprof_command)
        logger.debug("gprof_command:\n%s", self.gprof_command)
        os.system(self.gprof_linalg_command)
        logger.debug("gprof_linalg_command:\n%s", self.gprof_linalg_command)
        os.chdir("../")
        logger.debug("os.getcwd():\n%s", os.getcwd())
        with open(PYTHON_DIR + self.filename + ".py", "w") as f:
            f.write(self.original_code)
        sorter = ProfileResultSorter(self.gprof_out)
        sorter.process()
        sorter = ProfileResultSorter(self.gprof_linalg_out)
        sorter.process()
