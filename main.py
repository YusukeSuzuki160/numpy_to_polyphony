from code_translator import CodeTranslator
from last_translator import LastTranslator
import astor, ast
from np_lib_generator import NpLibGenerator
from polyphony_executer import PolyphonyExecuter
import sys


def main():
    filename = sys.argv[1].split('.')[0]
    code = open(filename + '.py').read()
    translator = CodeTranslator(code)
    translator.visit(translator.get_tree())
    tree = translator.get_tree()
    LastTranslator(translator.get_array_list(), translator.get_float_list(), translator.get_complex_list(), translator.get_npinstance_list()).visit(tree)
    # print(astor.dump_tree(tree))
    source = astor.to_source(tree)
    if not 'from polyphony import numpy' in source:
        source = 'from polyphony import numpy as np\n' + source
    if not 'from polyphony.typing import int8, int16, int32, int64, uint8, uint16, uint32, uint64, List, Tuple' in source:
        source = 'from polyphony.typing import int8, int16, int32, int64, uint8, uint16, uint32, uint64, List, Tuple\n' + source
    output_file = filename + '.polyphony.py'
    with open(output_file, 'w') as f:
        f.write(source)
    NpLibGenerator(translator.get_func_dict()).generate()
    PolyphonyExecuter(filename).execute()

if __name__ == '__main__':
    main()
