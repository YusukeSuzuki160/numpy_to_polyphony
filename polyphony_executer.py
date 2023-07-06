import os


class PolyphonyExecuter:
    def __init__(self, target):
        self.target = target + '.py'
        self.target_polyphony = target + '.polyphony.py'
        self.verilog_file = target + '.v'
        self.command = 'polyphony' + ' -o ' + self.verilog_file + ' ' + self.target_polyphony
        self.test_command = 'python3 ' + self.target
        self.verilog_command = 'iverilog -o ' + self.verilog_file + '.out ' + 'main.v' + ' ' + 'test.v'
    
    def execute(self):
        os.system(self.test_command)
        os.system(self.command)
        os.system(self.verilog_command)
        print('command: ' + self.verilog_command)
        os.system('./' + self.verilog_file + '.out')