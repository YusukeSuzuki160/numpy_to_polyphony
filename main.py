# Standard Library
import ast
import logging
import sys
from logging import getLogger

# Third Party Library
from code_translator import CodeTranslator
from polyphony_executer import PolyphonyExecuter


def main() -> None:
    logger = getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler("./numpy_to_polyphony/.log/main.log", mode="w")
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    try:
        file = sys.argv[1]
        filename = sys.argv[1].split(".")[-2]
        filename = filename.split("/")[-1]
        code = open(file).read()
        translator = CodeTranslator(code)
        translator.process()
        tree = translator.get_tree()
        lib_list = translator.get_lib_list()
        shapes = translator.get_shapes()
        source = ast.unparse(tree)
        import_stm = "from polyphony import testbench\nfrom polyphony.typing import int64\n"
        for lib in lib_list:
            import_stm += "import " + lib + "\n"
        source = import_stm + source
        logger.debug("source:\n%s", source)
        output_file = file.replace(".py", ".polyphony.py")
        with open(output_file, "w") as f:
            f.write(source)
        # NpLibGenerator(translator.get_func_dict()).generate()
        PolyphonyExecuter(filename, shapes).execute()
    except Exception as e:
        logger.exception(e)
        raise e


if __name__ == "__main__":
    main()
