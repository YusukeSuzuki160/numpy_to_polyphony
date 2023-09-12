import os, re

lib_file = 'list_fixed.py'
dir = os.path.dirname(__file__)

def generate_fixed_lib(col, row, lib_dir=dir):
    filename = 'list' + 'c' + str(col) + 'r' + str(row) + '.py'
    filepath = os.path.join(lib_dir, filename)
    code = open(os.path.join(dir, lib_file)).read()
    code = re.sub(r'COL = \d+', 'COL = ' + str(col), code)
    code = re.sub(r'ROW = \d+', 'ROW = ' + str(row), code)
    f = open(filepath, 'w')
    f.write(code)
    f.close()

def generate(shapes, lib_dir=dir):
    for (col, row) in shapes:
        generate_fixed_lib(col, row, lib_dir)

def clean(shapes):
    for (col, row) in shapes:
        filename = 'list_' + 'col' + str(col) + '_row' + str(row) + '.py'
        filepath = os.path.join(dir, filename)
        os.remove(filepath)


def gen_test():
    shapes = [(4, 4), (5, 5), (6, 6)]
    generate(shapes)

def clean_test():
    shapes = [(4, 4), (5, 5), (6, 6)]
    clean(shapes)

if __name__ == '__main__':
    gen_test()
    clean_test()