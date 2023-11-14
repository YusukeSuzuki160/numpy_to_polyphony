from typing import TypeAlias

VariableDict: TypeAlias = dict[str, dict[str, str | list[int]] | list[dict[str, str | list[int]]]]

Number: TypeAlias = int | float | complex
