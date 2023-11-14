# Standard Library
import argparse
import ast
import logging
from logging import getLogger

# Third Party Library
from code_translator import CodeTranslator
from config import Config
from polyphony_executer import PolyphonyExecuter
from polyphony_profiler import Profiler


def main() -> None:
    logger = getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler("./numpy_to_polyphony/.log/main.log", mode="w")
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--main", "-m")
    parser.add_argument("--config", "-c")
    parser.add_argument("--profile", "-p")
    args = parser.parse_args()
    main_func = args.main
    config = args.config
    if config is None:
        config = ""
    is_profile = bool(args.profile)
    if main_func is None:
        main_func = "main"
    logger.debug("main_func: %s", main_func)
    try:
        file = args.file
        filename = args.file.split(".")[-2]
        filename = filename.split("/")[-1]
        code = open(file).read()
        config = Config(config)
        translator = CodeTranslator(code, main_func, config)
        translator.process()
        tree = translator.get_tree()
        lib_list = translator.get_lib_list()
        shapes = translator.get_shapes()
        source = ast.unparse(tree)
        import_stm = (
            "from polyphony import testbench\nfrom polyphony.typing import int64\n"
        )
        for lib in lib_list:
            import_stm += "import " + lib + "\n"
        source = import_stm + source
        logger.debug("source:\n%s", source)
        output_file = filename + ".polyphony.py"
        output_file = "./polyphony-code/" + output_file
        with open(output_file, "w") as f:
            f.write(source)
        if is_profile:
            profiler = Profiler(source, output_file)
        else:
            profiler = None
        config = config.gen_config_json()
        PolyphonyExecuter(filename, shapes, config, profiler).execute()
    except Exception as e:
        logger.exception(e)
        raise e


if __name__ == "__main__":
    main()
