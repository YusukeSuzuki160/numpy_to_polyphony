import os
import re

class NpLibGenerator: # run at the super directory of polyphony-numpy
    def __init__(self, func_dict):
        self.func_dict = func_dict
        self.import_stm = 'from polyphony.typing import int8, int16, int32, int64, uint8, uint16, uint32, uint64, float16, float32, float64, complex64, complex128, bool_, List, Tuple\nfrom polyphony.timing import clkfence\n\n\n'
        self.func_list = []
        self.code = ''
        self.lib_name = '_numpy.py'
        self.lib_path = 'polyphony-numpy/polyphony/_internal/'
        self.exec_command = 'pip install polyphony-numpy/'

    def generate(self):
        self.generate_import()
        for func_name, func in self.func_dict.items():
            if func_name == 'main':
                continue
            elif func_name == 'array':
                self.generate_array(func)
            elif func_name == 'matmult':
                self.generate_matmult(func)
            elif func_name == 'print':
                self.generate_print(func)
            elif re.search('fixed', func_name):
                func_type = func_name.split('_')[1]
                self.generate_fixed(func, func_type)
        self.code = self.code[:-3]
        with open(self.lib_path + self.lib_name, 'w') as f:
            f.write(self.code)
        os.system(self.exec_command)

    def generate_import(self):
        self.code += self.import_stm
    
    def generate_array(self, func):
        arg_list = ''
        shape = func['shape']
        length = shape[0] * shape[1]
        dtype = func['dtype']
        for i in range(length):
            arg_list += 'a_' + str(i) + ', '
        return_stm = 'return ' + arg_list
        return_type = 'Tuple['
        for i in range(length):
            return_type += dtype + ', '
        return_type = return_type[:-2] + ']'
        function_name = 'array' + '_' + str(length) + '_' + dtype
        func_str = 'def ' + function_name + '(' + arg_list + ') -> ' + return_type + ':\n'
        func_str += '\t' + return_stm
        self.func_list.append(func_str)
        self.code += func_str + '\n\n\n'
    
    def generate_matmult(self, func):
        arg_list = ''
        left_shape = func['shape1']
        right_shape = func['shape2']
        dtype = func['dtype']
        return_shape = (left_shape[0], right_shape[1])
        length = return_shape[0] * return_shape[1]
        for i in range(length):
            arg_list += 'a_' + str(i) + ', '
        for i in range(length):
            arg_list += 'b_' + str(i) + ', '
        return_args = ''
        return_type = 'Tuple['
        for i in range(length):
            return_args += 'c_' + str(i) + ', '
            return_type += dtype + ', '
        return_stm = 'return ' + return_args
        shapes = '_' + 'l' + str(left_shape[0]) + '_' + str(left_shape[1]) + '_' + 'r' + str(right_shape[0]) + '_' + str(right_shape[1])
        func_name = 'matmult' + shapes + '_' + dtype
        func_str = 'def ' + func_name + '(' + arg_list + ') -> ' + return_type[:-2] + ']:\n'
        for i in range(return_shape[0] * return_shape[1]):
            func_str += '\tc_' + str(i) + ' = 0\n'
        count = 0
        for i in range(return_shape[0]):
            for j in range(return_shape[1]):
                for k in range(left_shape[1]):
                    func_str += '\td_' + str(count) + ' = 0\n'
                    count += 1
        count = 0

        func_str += '\tclkfence()\n'
        for i in range(return_shape[0]):
            for j in range(return_shape[1]):
                for k in range(left_shape[1]):
                    func_str += '\td_' + str(count) + ' = a_' + str(i * left_shape[1] + k) + ' * b_' + str(k * right_shape[1] + j) + '\n'
                    count += 1
        count = 0
        func_str += '\tclkfence()\n'
        for i in range(return_shape[0]):
            for j in range(return_shape[1]):
                func_str += '\tc_' + str(i * return_shape[1] + j) + ' = '
                for k in range(left_shape[1]):
                    func_str += 'd_' + str(count) + ' + '
                    count += 1
                func_str = func_str[:-3] + '\n'
        func_str += '\t' + return_stm
        self.func_list.append(func_str)
        self.code += func_str + '\n\n\n'

    def generate_print(self, func):
        arg_list = ''
        shape = func['shape']
        length = shape[0] * shape[1]
        dtype = func['dtype']
        for i in range(length):
            arg_list += 'a_' + str(i) + ', '
        func_name = '_print' + '_' + str(length) + '_' + dtype
        func_str = 'def ' + func_name + '(' + arg_list + ') -> None:\n'
        for i in range(length):
            func_str += '\tprint(a_' + str(i) + ')\n'
        self.func_list.append(func_str)
        self.code += func_str + '\n\n\n'

    def generate_fixed(self, func, func_type):
        type = func['dtype']
        if func_type == 'add':
            func_str = self.fixed_add(type)

    def fixed_add(self, type):
        if type == 'fixed64':
            self.code += 'def fixed64_add(a: int64, b: int64) -> int64:\n\
    return a + b\n\n\n'