from code_translator import CodeTranslator
from last_translator import LastTranslator, ReturnAnalyzer, AddArgsDifinition
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
    return_analyzer = ReturnAnalyzer(translator.get_array_list(), translator.get_float_list(), translator.get_complex_list(), translator.get_npinstance_list())
    return_analyzer.visit(tree)
    last_traslator = LastTranslator(translator.get_array_list(), translator.get_float_list(), translator.get_complex_list(), translator.get_npinstance_list(), return_analyzer.returns)
    last_traslator.visit(tree)
    AddArgsDifinition(last_traslator.add_args).visit(tree)
    # print(astor.dump_tree(tree))
    source = astor.to_source(tree)
    nplibs = NpLibGenerator(translator.get_func_dict())
    source = nplibs.generate() + source
    if not 'from polyphony.typing import int8, int16, int32, int64, uint8, uint16, uint32, uint64, List, Tuple' in source:
        source = 'from polyphony.typing import int8, int16, int32, int64, uint8, uint16, uint32, uint64, List, Tuple\n' + source
    
    output_file = filename + '.polyphony.py'
    with open(output_file, 'w') as f:
        f.write(source)
    PolyphonyExecuter(filename).execute()

if __name__ == '__main__':
    main()
