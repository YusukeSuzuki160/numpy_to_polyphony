from code_translator import CodeTranslator
from last_translator import LastTranslator
import astor
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
    source = astor.to_source(tree)
    output_file = filename + '.polyphony.py'
    with open(output_file, 'w') as f:
        f.write(source)
    NpLibGenerator(translator.get_func_dict()).generate()
    PolyphonyExecuter(filename).execute()

if __name__ == '__main__':
    main()
