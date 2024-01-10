import os
import re

lib_file = "list_fixed.py"
lib_horizonal_file = "list_horizonal.py"
lib_vertical_file = "list_vertical.py"
dir = os.path.dirname(__file__)

generated = []


def generate_fixed_lib(col: int, row: int, lib_dir: str = dir) -> None:
    filename = "list" + "c" + str(col) + "r" + str(row) + ".py"
    if filename in generated:
        return
    generated.append(filename)
    filepath = os.path.join(lib_dir, filename)
    if row == 1:
        code = open(os.path.join(dir, lib_horizonal_file)).read()
        code = re.sub(r"LEN: int16 = \d+", "LEN: int16 = " + str(col), code)
    elif col == 1:
        code = open(os.path.join(dir, lib_vertical_file)).read()
        code = re.sub(r"LEN: int16 = \d+", "LEN: int16 = " + str(row), code)
    else:
        code = open(os.path.join(dir, lib_file)).read()
        code = re.sub(r"COL: int8 = \d+", "COL: int8 = " + str(col), code)
        code = re.sub(r"ROW: int8 = \d+", "ROW: int8 = " + str(row), code)
    if row != 1:
        import_linalg = "import list" + "c" + str(col) + "r" + "1" + " as list_linalg"
        code = import_linalg + "\n" + code
    else:
        code = re.sub(r"list_linalg_qr\.", "", code)
    f = open(filepath, "w")
    f.write(code)
    f.close()
    if row != 1:
        generate_fixed_lib(col, 1, lib_dir)


def generate(shapes: list[tuple[int, int]], lib_dir: str = dir) -> None:
    for col, row in shapes:
        generate_fixed_lib(col, row, lib_dir)


def clean(shapes: list[tuple[int, int]]) -> None:
    for col, row in shapes:
        filename = "list_" + "col" + str(col) + "_row" + str(row) + ".py"
        filepath = os.path.join(dir, filename)
        os.remove(filepath)


def gen_test() -> None:
    shapes = [(4, 4), (5, 5), (6, 6)]
    generate(shapes)


def clean_test() -> None:
    shapes = [(4, 4), (5, 5), (6, 6)]
    clean(shapes)


if __name__ == "__main__":
    gen_test()
    clean_test()
