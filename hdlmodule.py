import os


class HDLAction:
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        return "HDLAction"


class HDLVariable(HDLAction):
    def __init__(self, name: str, width: int, type: str, signed: bool = False) -> None:
        self.name = name
        self.width = width
        self.type = type
        self.signed = signed

    def __str__(self) -> str:
        return f"{self.name}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HDLVariable):
            return NotImplemented
        return (
            self.name == other.name
            and self.width == other.width
            and self.type == other.type
        )

    def gen_decl(self) -> str:
        if self.signed:
            if self.width == 1:
                return f"{self.type} signed {self.name}"
            else:
                return f"{self.type} signed [{self.width-1}:0] {self.name}"
        else:
            if self.width == 1:
                return f"{self.type} {self.name}"
            else:
                return f"{self.type} [{self.width-1}:0] {self.name}"

    def gen_init(self) -> str:
        if self.type == "reg":
            return f"{self.name} <= 0;"
        else:
            return ""


class HDLList(HDLVariable):
    def __init__(self, name: str, width: int, len: int, signed: bool = False) -> None:
        super().__init__(name, width, "reg", signed=signed)
        self.len = len

    def __str__(self) -> str:
        return f"{self.name}[{self.len-1}:0]"

    def gen_decl(self) -> str:
        return super().gen_decl() + f"[0:{self.len-1}]"

    def gen_init(self) -> str:
        if self.type == "reg":
            return f"for (integer i = 0; i < {self.len}; i++) begin\n    {self.name}[i] <= 0;\nend"
        else:
            return ""


class HDLBlockingAssign(HDLAction):
    def __init__(self, lhs: str, rhs: str) -> None:
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self) -> str:
        return f"{self.lhs} = {self.rhs};"


class HDLNonBlockingAssign(HDLAction):
    def __init__(self, lhs: str, rhs: str) -> None:
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self) -> str:
        return f"{self.lhs} <= {self.rhs};"


class HDLIndexAccess(HDLAction):
    def __init__(self, var: str, index: str) -> None:
        self.var = var
        self.index = index

    def __str__(self) -> str:
        return f"{self.var}[{self.index}]"


class HDLIfElse(HDLAction):
    def __init__(self) -> None:
        self.conds = []
        self.actions: list[list[HDLAction]] = []

    def __str__(self) -> str:
        s = ""
        for i in range(len(self.conds)):
            if self.conds[i] == "1":
                for action in self.actions[i]:
                    s += f"{action}\n"
            else:
                s += f"if ({self.conds[i]}) begin\n"
                for action in self.actions[i]:
                    s += f"    {action}\n"
                s += "end\n"
        if len(self.actions) > len(self.conds):
            s += "else begin\n"
            for action in self.actions[-1]:
                s += f"    {action}\n"
            s += "end\n"
        return s

    def add_action(self, cond: str, action: HDLAction) -> None:
        if cond not in self.conds:
            self.conds.append(cond)
            self.actions.append([])
        self.actions[self.conds.index(cond)].append(action)


class HDLModule:
    # have to get input when state == idle and ready == 1
    # have to set valid = 1 when all outputs are ready
    # if accept == 1, set state = idle
    def __init__(self, name: str) -> None:
        self.name = name
        self.func_name = name.split("_")[1]
        self.ports: list[HDLVariable] = [
            HDLVariable("clk", 1, "input wire"),
            HDLVariable("rst", 1, "input wire"),
            HDLVariable(self.func_name + "_ready", 1, "input wire"),
            HDLVariable(self.func_name + "_accept", 1, "input wire"),
            HDLVariable(self.func_name + "_valid", 1, "output reg"),
        ]
        self.registers: list[HDLVariable] = []
        self.wires: list[HDLVariable] = []
        self.always_do: list[HDLAction] = []
        self.dataflow: dict[str, list[HDLAction]] = {
            "idle": [HDLNonBlockingAssign(self.func_name + "_valid", "0")],
            "fin": [HDLNonBlockingAssign(self.func_name + "_valid", "1")],
        }
        self.controlflow: dict[str, dict[str, str]] = {
            "fin": {self.func_name + "_accept": "idle"}
        }
        self.assigns: list[HDLBlockingAssign] = []
        self.states: dict[str, int] = {"idle": 0, "fin": 1}
        self.state_count = 2
        self.verilog_path = (
            os.path.abspath("./numpy_to_polyphony/verilog/") + "/" + name + ".v"
        )

    def add_port(self, name: str, width: int, type: str, signed: bool = False) -> None:
        variable = HDLVariable(name, width, type, signed=signed)
        if variable not in self.ports:
            self.ports.append(variable)

    def add_register(self, name: str, width: int, signed: bool = False) -> None:
        variable = HDLVariable(name, width, "reg")
        if variable not in self.registers:
            self.registers.append(variable)

    def add_list(self, name: str, width: int, len: int, signed: bool = False) -> None:
        variable = HDLList(name, width, len)
        if variable not in self.registers:
            self.registers.append(variable)

    def add_wire(self, name: str, width: int, signed: bool = False) -> None:
        variable = HDLVariable(name, width, "wire")
        if variable not in self.wires:
            self.wires.append(variable)

    def state(self, name: str) -> str:
        if name not in self.states:
            self.states[name] = self.state_count
            self.state_count += 1
        return name

    def add_dataflow(self, name: str, action: HDLAction) -> None:
        name = self.state(name)
        if name not in self.dataflow:
            self.dataflow[name] = []
        self.dataflow[name].append(action)

    def add_controlflow(self, name: str, cond: str, next_state: str) -> None:
        name = self.state(name)
        if name not in self.controlflow:
            self.controlflow[name] = {}
        self.controlflow[name][cond] = self.state(next_state)

    def add_assign(self, lhs: str, rhs: str) -> None:
        self.assigns.append(HDLBlockingAssign(lhs, rhs))

    def add_always_do(self, action: HDLAction) -> None:
        self.always_do.append(action)

    def build(self) -> str:
        state_width = len(bin(self.state_count - 1)[2:])
        self.add_register("state", state_width)
        return str(self)

    def generate(self) -> None:
        with open(self.verilog_path, mode="w") as f:
            f.write(self.build())

    def __str__(self) -> str:
        s = f"module {self.name} (\n"
        for port in self.ports:
            s += f"    {port.gen_decl()},\n"
        s = s[:-2] + "\n);\n"
        for state, state_int in self.states.items():
            s += f"    localparam {state} = {state_int};\n"
        for register in self.registers:
            s += f"    {register.gen_decl()};\n"
        for wire in self.wires:
            s += f"    {wire.gen_decl()};\n"
        s += "\n"
        for assign in self.assigns:
            s += f"    assign {assign}\n"
        s += "\n"
        s += "    always @(posedge clk) begin\n"
        s += "        if (rst) begin\n"
        for register in self.registers:
            s += f"            {register.gen_init()}\n"
        for port in self.ports:
            if port.type == "output reg":
                s += f"            {port.name} <= 0;\n"
        s += "        end else begin\n"
        for action in self.always_do:
            s += f"            {action}\n"
        s += "            case (state)\n"
        for state, actions in self.dataflow.items():
            s += f"                {state}: begin\n"
            for action in actions:
                s += f"                    {action}\n"
            s += "                end\n"
        s += "            endcase\n"
        s += "        end\n"
        s += "    end\n"
        s += "\n"
        s += "    always @(posedge clk) begin\n"
        s += "        if (rst) begin\n"
        s += f"            state <= {self.states['idle']};\n"
        s += "        end else begin\n"
        s += "            case (state)\n"
        for state, conds in self.controlflow.items():
            for cond, next_state in conds.items():
                if cond == "1":
                    s += f"                {state}: begin\n"
                    s += f"                    state <= {next_state};\n"
                    s += "                end\n"
                else:
                    s += f"                {state}: begin\n"
                    s += f"                    if ({cond}) begin\n"
                    s += f"                        state <= {next_state};\n"
                    s += "                    end\n"
                    s += "                end\n"
        s += "            endcase\n"
        s += "        end\n"
        s += "    end\n"
        s += "\n"
        s += "endmodule\n"
        return s


def test() -> None:
    test_module = HDLModule("int_add")
    test_module.add_port("a", 32, "input wire")
    test_module.add_port("b", 32, "input wire")
    test_module.add_port("c", 32, "output reg")
    test_module.add_register("d", 32)
    test_module.add_wire("e", 32)
    test_module.add_assign("e", "2 * d")
    test_module.add_dataflow("idle", HDLNonBlockingAssign("c", "0"))
    test_module.add_dataflow("calc", HDLNonBlockingAssign("d", "a + b"))
    test_module.add_dataflow("fin", HDLNonBlockingAssign("c", "d"))
    test_module.add_controlflow("idle", "add_ready == 1", "calc")
    test_module.add_controlflow("calc", "1", "fin")

    print(test_module.build())
    test_module.generate()


if __name__ == "__main__":
    test()
