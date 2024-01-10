import ast
import math

BIT_WIDTH = 64

class DivisionOptimizer(ast.NodeTransformer):
    def __init__(self, constant_dict: dict[str, int], globals: list[str] = []):
        self.constant_dict = constant_dict
        self.globals = globals
        self.current_func = ""

    def visit_FunctionDef(self, node):
        self.current_func = node.name
        node = self.generic_visit(node)
        self.current_func = ""
        return node

    def visit_Assign(self, node):
        node = self.generic_visit(node)
        if isinstance(node.value, ast.BinOp):
            binop_node = node.value
            if isinstance(binop_node.op, ast.FloorDiv):
                if isinstance(binop_node.right, ast.Constant):
                    value = binop_node.right.value
                elif isinstance(binop_node.right, ast.Name):
                    if binop_node.right.id in self.globals:
                        id = "." + binop_node.right.id
                    else:
                        id = self.current_func + "." + binop_node.right.id
                    value = self.constant_dict[id]
                elif isinstance(binop_node.right, ast.BinOp):
                    left = binop_node.right.left
                    right = binop_node.right.right
                    if isinstance(left, ast.Constant):
                        left_value = left.value
                    elif isinstance(left, ast.Name):
                        if left.id in self.globals:
                            id = "." + left.id
                        else:
                            id = self.current_func + "." + left.id
                        left_value = self.constant_dict[id]
                    else:
                        return node
                    if isinstance(right, ast.Constant):
                        right_value = right.value
                    elif isinstance(right, ast.Name):
                        if right.id in self.globals:
                            id = "." + right.id
                        else:
                            id = self.current_func + "." + right.id
                        right_value = self.constant_dict[id]
                    match binop_node.right.op:
                        case ast.Add():
                            value = left_value + right_value
                        case ast.Sub():
                            value = left_value - right_value
                        case ast.Mult():
                            value = left_value * right_value
                        case ast.Div():
                            value = left_value / right_value
                        case _:
                            return node
                if isinstance(node.targets[0], ast.Name):
                    target_id = node.targets[0].id
                elif isinstance(node.targets[0], ast.Subscript):
                    target_id = node.targets[0].value.id + "[" + ast.unparse(node.targets[0].slice) + "]"
                if value == 1:
                    return ast.copy_location(ast.parse(f"{target_id} = {binop_node.left.id}"), node)
                elif value & (value - 1) == 0:
                    return ast.copy_location(ast.parse(f"{target_id} = {binop_node.left.id} >> {int(math.log2(value))}"), node)
                else:
                    l = math.floor(math.log2(value))
                    m = math.floor(2 ** (BIT_WIDTH + l) / value)
                    if value < 0:
                        code = f"""
_tmp: int{2 * BIT_WIDTH} = {binop_node.left.id} * {m - (1 << BIT_WIDTH)}
_tmp = _tmp >> {BIT_WIDTH}
_tmp = {binop_node.left.id} + _tmp
# if {binop_node.left.id} < 0:
#     {target_id} = -(_tmp >> {l}) - 1
# else:
#     {target_id} = -(_tmp >> {l})
{target_id} = -(_tmp >> {l})
"""
                    else:
                        code = f"""
_tmp: int{2 * BIT_WIDTH} = {binop_node.left.id} * {m - (1 << BIT_WIDTH)}
_tmp = _tmp >> {BIT_WIDTH}
_tmp = {binop_node.left.id} + _tmp
# if {binop_node.left.id} < 0:
#     {target_id} = (_tmp >> {l}) + 1
# else:
#     {target_id} = _tmp >> {l}
{target_id} = _tmp >> {l}
"""
                    return ast.parse(code).body
            else:
                return node
        else:
            return node