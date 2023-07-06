from _ast import Import
import ast
from typing import Any

class LastTranslator(ast.NodeTransformer):
    def visit_Import(self, node: Import) -> Any:
        if node.names[0].name == 'numpy':
            return ast.ImportFrom(module='polyphony', names=[ast.alias(name='numpy', asname='np')], level=0)